"""Optional fine-tuned transformer classifier with an honest keyword baseline fallback."""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

CATEGORIES = [
    "Payment", "Liability", "Termination", "Confidentiality", "Intellectual Property",
    "Data Protection", "Dispute Resolution", "Governing Law", "Restrictive Covenant",
    "Indemnification", "Warranty", "Other",
]

PATTERNS: dict[str, list[str]] = {
    "Payment": [r"\bpayment\b", r"\bpayable\b", r"\binvoice\b", r"\bfees?\b", r"\bprice\b", r"\bconsideration\b", r"\bremittance\b", r"\binterest on late\b"],
    "Liability": [r"\bliabilit(?:y|ies)\b", r"\blimit(?:ation)? of liability\b", r"\bliability cap\b", r"\bconsequential damages\b", r"\bindirect damages\b", r"\buncapped\b"],
    "Termination": [r"\bterminat(?:e|ion|ed|ing)\b", r"\bexpires?\b", r"\bexpiration\b", r"\brenew(?:al|ed)\b", r"\bnotice period\b", r"\bsurvive termination\b"],
    "Confidentiality": [r"\bconfidential(?:ity)?\b", r"\bnon.?disclosure\b", r"\btrade secret\b", r"\bproprietary information\b", r"\bdisclos(?:e|ure)\b"],
    "Intellectual Property": [r"\bintellectual property\b", r"\bwork product\b", r"\bcopyright\b", r"\bpatent\b", r"\btrademark\b", r"\bassign(?:ment)? of (?:all )?(?:right|invention|ip)\b", r"\blicen[cs]e\b"],
    "Data Protection": [r"\bpersonal data\b", r"\bdata protection\b", r"\bdata processor\b", r"\bdata fiduciary\b", r"\bprivacy\b", r"\bsecurity breach\b", r"\bprocess(?:ing)? of data\b"],
    "Dispute Resolution": [r"\barbitration\b", r"\barbitral\b", r"\bdispute resolution\b", r"\bmediation\b", r"\bjurisdiction of (?:the )?courts?\b", r"\bseat of arbitration\b"],
    "Governing Law": [r"\bgoverned by (?:the )?laws? of\b", r"\bgoverning law\b", r"\bchoice of law\b", r"\bconstrued in accordance with\b"],
    "Restrictive Covenant": [r"\bnon.?compete\b", r"\bnon.?solicit\b", r"\brestraint of trade\b", r"\bexclusive(?:ly|ness)?\b", r"\bnot compete\b", r"\bsolicit(?:ation)?\b"],
    "Indemnification": [r"\bindemnif(?:y|ication|ied|ies)\b", r"\bhold harmless\b", r"\bdefend and indemnify\b"],
    "Warranty": [r"\bwarrant(?:y|ies|s|ed)\b", r"\bworkmanlike\b", r"\bfitness for purpose\b", r"\bmerchantability\b", r"\bdefect(?:s|ive)?\b"],
}


class ClauseClassifier:
    def __init__(self, checkpoint: str = ""):
        self.checkpoint = checkpoint.strip()
        self.engine = "keyword_baseline"
        self.model = None
        self.tokenizer = None
        self.labels = CATEGORIES
        self._implementation_fingerprint = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        self._checkpoint_manifest = self._build_checkpoint_manifest()
        if self.checkpoint and Path(self.checkpoint).exists():
            self._load_local_model()

    def _build_checkpoint_manifest(self) -> list[dict[str, Any]]:
        if not self.checkpoint:
            return []
        root = Path(self.checkpoint).expanduser()
        if not root.exists():
            return [{"missing": str(root.resolve())}]
        try:
            files = [root] if root.is_file() else sorted(path for path in root.rglob("*") if path.is_file())
            manifest = []
            for path in files:
                stat = path.stat()
                name = path.name if root.is_file() else str(path.relative_to(root))
                manifest.append({"name": name, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns})
            return manifest
        except OSError:
            return [{"unreadable": str(root.resolve())}]

    @property
    def configuration_fingerprint(self) -> str:
        """Stable signature for the active classifier code and local checkpoint manifest."""
        checkpoint = str(Path(self.checkpoint).expanduser().resolve()) if self.checkpoint else ""
        settings = {
            "engine": self.engine,
            "checkpoint": checkpoint,
            "checkpoint_manifest": self._checkpoint_manifest,
            "labels": self.labels,
            "patterns": PATTERNS if self.engine == "keyword_baseline" else None,
            "implementation_sha256": self._implementation_fingerprint,
        }
        encoded = json.dumps(settings, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _load_local_model(self) -> None:
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(self.checkpoint, local_files_only=True)
            model = AutoModelForSequenceClassification.from_pretrained(self.checkpoint, local_files_only=True)
            raw = model.config.id2label or {}
            labels = [str(raw.get(i, raw.get(str(i), ""))) for i in range(model.config.num_labels)]
            if not labels or any(not label or label.upper().startswith("LABEL_") for label in labels):
                return
            model.eval()
            self.model, self.tokenizer, self.labels = model, tokenizer, labels
            self._torch = torch
            self.engine = "fine_tuned_transformer"
        except Exception:
            # A missing checkpoint or base-only LegalBERT must not be presented as a trained classifier.
            self.model = None
            self.tokenizer = None
            self.engine = "keyword_baseline"

    def classify(self, text: str) -> dict[str, Any]:
        if self.model is not None:
            try:
                encoded = self.tokenizer(text[:12000], return_tensors="pt", truncation=True, max_length=512)
                with self._torch.no_grad():
                    logits = self.model(**encoded).logits[0]
                    probs = self._torch.softmax(logits, dim=-1).cpu().tolist()
                index = max(range(len(probs)), key=probs.__getitem__)
                return {"category": self.labels[index], "confidence": round(float(probs[index]), 4),
                        "engine": self.engine, "signals": []}
            except Exception:
                # Report the fallback engine truthfully if a loaded checkpoint
                # becomes unusable during inference.
                self.model = None
                self.tokenizer = None
                self.engine = "keyword_baseline"
        return self._keyword_classify(text)

    @staticmethod
    def _keyword_classify(text: str) -> dict[str, Any]:
        normalized = re.sub(r"\s+", " ", text.lower())
        scores: dict[str, float] = defaultdict(float)
        hits: dict[str, list[str]] = defaultdict(list)
        for category, patterns in PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, normalized):
                    scores[category] += 1.0
                    hits[category].append(re.sub(r"\\b|\\s\+", "", pattern))
        if not scores:
            return {"category": "Other", "confidence": 0.25, "engine": "keyword_baseline", "signals": []}
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        category, score = ranked[0]
        confidence = min(0.72, 0.34 + 0.11 * score + (0.08 if len(ranked) == 1 else 0))
        return {"category": category, "confidence": round(confidence, 3),
                "engine": "keyword_baseline", "signals": hits[category][:5]}

    @property
    def description(self) -> str:
        if self.engine == "fine_tuned_transformer":
            return f"Fine-tuned local Hugging Face sequence classifier: {Path(self.checkpoint).name}"
        return "Transparent keyword baseline; no trained LegalBERT model is bundled"


def clause_risk_hint(text: str, category: str) -> tuple[str, list[str]]:
    """Non-probabilistic review-priority hint; never a legal finding."""
    lower = text.lower()
    signals: list[str] = []
    high_terms = ["unlimited liability", "without limitation", "sole discretion", "indemnify", "hold harmless",
                  "perpetual", "irrevocable", "waive any and all", "at any time without cause"]
    for term in high_terms:
        if term in lower:
            signals.append(term)
    if signals:
        return "high", signals[:4]
    sensitive = {"Payment", "Liability", "Termination", "Data Protection", "Restrictive Covenant", "Indemnification"}
    if category in sensitive:
        return "medium", ["Clause type commonly merits review; context-specific assessment required."]
    return "low", ["No baseline review trigger; not an assurance of low legal risk."]
