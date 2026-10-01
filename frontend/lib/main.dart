import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:file_saver/file_saver.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';

import 'api_client.dart';

final apiProvider = Provider<ApiClient>((ref) => ApiClient());
final contractsProvider = FutureProvider<List<Map<String, dynamic>>>(
  (ref) => ref.watch(apiProvider).contracts(),
);
final dashboardStatsProvider = FutureProvider<Map<String, dynamic>>(
  (ref) => ref.watch(apiProvider).stats(),
);

const ink = Color(0xFF183139);
const teal = Color(0xFF0D887E);
const paper = Color(0xFFF7F9F7);

const _indianJurisdictions = <String>[
  'Andhra Pradesh',
  'Arunachal Pradesh',
  'Assam',
  'Bihar',
  'Chhattisgarh',
  'Goa',
  'Gujarat',
  'Haryana',
  'Himachal Pradesh',
  'Jharkhand',
  'Karnataka',
  'Kerala',
  'Madhya Pradesh',
  'Maharashtra',
  'Manipur',
  'Meghalaya',
  'Mizoram',
  'Nagaland',
  'Odisha',
  'Punjab',
  'Rajasthan',
  'Sikkim',
  'Tamil Nadu',
  'Telangana',
  'Tripura',
  'Uttar Pradesh',
  'Uttarakhand',
  'West Bengal',
  'Andaman and Nicobar Islands',
  'Chandigarh',
  'Dadra and Nagar Haveli and Daman and Diu',
  'Delhi',
  'Jammu and Kashmir',
  'Ladakh',
  'Lakshadweep',
  'Puducherry',
  'Other / multi-state',
];

const _contractTypes = <String, String>{
  'nda': 'NDA',
  'employment': 'Employment',
  'vendor': 'Vendor / service',
  'consultancy': 'Consultancy',
  'saas_it': 'SaaS / IT',
  'procurement': 'Procurement',
  'lease': 'Lease / rental',
  'data_processing': 'Data processing',
  'other': 'Other',
};

void main() => runApp(const ProviderScope(child: ContractSenseApp()));

class ContractSenseApp extends StatelessWidget {
  const ContractSenseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ContractSense',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: teal, surface: paper),
        scaffoldBackgroundColor: paper,
        useMaterial3: true,
        appBarTheme: const AppBarTheme(
          backgroundColor: paper,
          foregroundColor: ink,
          elevation: 0,
        ),
        cardTheme: CardThemeData(
          color: Colors.white,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: const BorderSide(color: Color(0xFFE6ECE9)),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(11),
            borderSide: const BorderSide(color: Color(0xFFE1E9E5)),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(11),
            borderSide: const BorderSide(color: Color(0xFFE1E9E5)),
          ),
        ),
      ),
      home: const AuthGate(),
    );
  }
}

class AuthGate extends ConsumerStatefulWidget {
  const AuthGate({super.key});

  @override
  ConsumerState<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends ConsumerState<AuthGate> {
  bool _checking = true;
  Map<String, dynamic>? _user;

  @override
  void initState() {
    super.initState();
    _restoreSession();
  }

  Future<void> _restoreSession() async {
    try {
      _user = await ref.read(apiProvider).me();
    } catch (_) {
      _user = null;
    }
    if (mounted) setState(() => _checking = false);
  }

  @override
  Widget build(BuildContext context) {
    if (_checking) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return _user == null ? const AuthScreen() : HomeScreen(user: _user!);
  }
}

class AuthScreen extends ConsumerStatefulWidget {
  const AuthScreen({super.key});

  @override
  ConsumerState<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends ConsumerState<AuthScreen> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _register = false;
  bool _loading = false;

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      final api = ref.read(apiProvider);
      final data = _register
          ? await api.register(_name.text.trim(), _email.text.trim(), _password.text)
          : await api.login(_email.text.trim(), _password.text);
      if (!mounted) return;
      final user = _asMap(data['user']);
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => HomeScreen(user: user)),
      );
    } catch (error) {
      if (mounted) _showSnack(context, friendlyError(error), error: true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 440),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(28),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const _Brand(),
                      const SizedBox(height: 28),
                      Text(
                        _register ? 'Create your workspace' : 'Welcome back',
                        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                              fontWeight: FontWeight.w800,
                              color: ink,
                            ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        _register
                            ? 'Keep your contract reviews in one private place.'
                            : 'Sign in to continue your contract review.',
                        style: const TextStyle(color: Colors.black54),
                      ),
                      const SizedBox(height: 24),
                      if (_register) ...[
                        TextFormField(
                          controller: _name,
                          decoration: const InputDecoration(labelText: 'Full name'),
                          validator: (value) => value == null || value.trim().isEmpty
                              ? 'Enter your name'
                              : null,
                        ),
                        const SizedBox(height: 14),
                      ],
                      TextFormField(
                        controller: _email,
                        keyboardType: TextInputType.emailAddress,
                        autofillHints: const [AutofillHints.email],
                        decoration: const InputDecoration(labelText: 'Email'),
                        validator: (value) => value == null || !value.contains('@')
                            ? 'Enter a valid email'
                            : null,
                      ),
                      const SizedBox(height: 14),
                      TextFormField(
                        controller: _password,
                        obscureText: true,
                        autofillHints: _register
                            ? const [AutofillHints.newPassword]
                            : const [AutofillHints.password],
                        decoration: const InputDecoration(labelText: 'Password'),
                        validator: (value) => value == null || value.length < 10
                            ? 'Use at least 10 characters'
                            : null,
                      ),
                      const SizedBox(height: 20),
                      SizedBox(
                        width: double.infinity,
                        child: FilledButton(
                          onPressed: _loading ? null : _submit,
                          child: _loading
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                )
                              : Text(_register ? 'Create account' : 'Sign in'),
                        ),
                      ),
                      Center(
                        child: TextButton(
                          onPressed: () => setState(() => _register = !_register),
                          child: Text(
                            _register
                                ? 'Already have an account? Sign in'
                                : 'Create an account',
                          ),
                        ),
                      ),
                      const Text(
                        'ContractSense is an informational decision-support tool, not legal advice.',
                        style: TextStyle(fontSize: 11, color: Colors.black45),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key, required this.user});

  final Map<String, dynamic> user;

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  bool _loading = true;
  List<Map<String, dynamic>> _contracts = [];
  Map<String, dynamic> _stats = {};

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    if (mounted) setState(() => _loading = true);
    try {
      final contracts = await ref.refresh(contractsProvider.future);
      final stats = await ref.refresh(dashboardStatsProvider.future);
      if (!mounted) return;
      setState(() {
        _contracts = contracts;
        _stats = stats;
      });
    } catch (error) {
      if (mounted) _showSnack(context, friendlyError(error), error: true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _signOut() async {
    await ref.read(apiProvider).logout();
    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const AuthScreen()),
      (_) => false,
    );
  }

  Future<void> _upload() async {
    final picked = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'tif', 'tiff'],
      withData: true,
    );
    if (picked == null || !mounted) return;

    final file = picked.files.single;
    final Uint8List? bytes = file.bytes;
    if (bytes == null) {
      _showSnack(context, 'Could not read the selected file.', error: true);
      return;
    }

    final metadata = await showDialog<_UploadMetadata>(
      context: context,
      builder: (_) => const _UploadDialog(),
    );
    if (metadata == null || !mounted) return;

    try {
      _showSnack(context, 'Extracting text and analyzing…');
      final uploaded = await ref.read(apiProvider).upload(
            name: file.name,
            bytes: bytes,
            type: metadata.type,
            state: metadata.state,
            governingLaw: metadata.governingLaw,
            msmeSupplier: metadata.msmeSupplier,
          );
      final contract = _asMap(uploaded['contract']);
      final analysis = await ref.read(apiProvider).analyze(contract['id'].toString());
      await _refresh();
      if (!mounted) return;
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ContractDetailScreen(
            contract: contract,
            result: _asMap(analysis['result']),
          ),
        ),
      );
    } catch (error) {
      if (mounted) _showSnack(context, friendlyError(error), error: true);
    }
  }

  Future<void> _openContract(Map<String, dynamic> row) async {
    try {
      final response = await ref.read(apiProvider).contract(row['id'].toString());
      final contract = _asMap(response['contract']);
      var result = response['analysis'];
      if (result == null) {
        final analysis = await ref.read(apiProvider).analyze(row['id'].toString());
        result = analysis['result'];
      }
      if (!mounted) return;
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ContractDetailScreen(
            contract: contract,
            result: _asMap(result),
          ),
        ),
      );
    } catch (error) {
      if (mounted) _showSnack(context, friendlyError(error), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final firstName = (widget.user['full_name'] ?? 'there').toString().split(' ').first;
    return Scaffold(
      appBar: AppBar(
        title: const _Brand(),
        actions: [
          IconButton(
            onPressed: _signOut,
            icon: const Icon(Icons.logout_rounded),
            tooltip: 'Sign out',
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _upload,
        icon: const Icon(Icons.add),
        label: const Text('Review contract'),
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(18, 10, 18, 100),
                children: [
                  Text(
                    'YOUR CONTRACT DESK',
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          letterSpacing: 1.5,
                          color: teal,
                          fontWeight: FontWeight.w800,
                        ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Good day, $firstName.',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                          fontWeight: FontWeight.w800,
                          color: ink,
                        ),
                  ),
                  const SizedBox(height: 7),
                  const Text(
                    'Start with the clauses that deserve a closer look.',
                    style: TextStyle(color: Colors.black54),
                  ),
                  const SizedBox(height: 20),
                  Wrap(
                    spacing: 10,
                    runSpacing: 10,
                    children: [
                      _StatCard(
                        label: 'Contracts',
                        value: '${_stats['contracts_total'] ?? 0}',
                        icon: Icons.description_outlined,
                      ),
                      _StatCard(
                        label: 'Analyzed',
                        value: '${_stats['analyzed_total'] ?? 0}',
                        icon: Icons.task_alt,
                      ),
                      _StatCard(
                        label: 'High-priority reviews',
                        value: '${_stats['high_priority_total'] ?? 0}',
                        icon: Icons.priority_high,
                      ),
                      _StatCard(
                        label: 'Average score',
                        value: _stats['analyzed_total'] == 0
                            ? '—'
                            : '${_stats['average_risk_score'] ?? 0}/100',
                        icon: Icons.donut_large,
                      ),
                    ],
                  ),
                  const SizedBox(height: 22),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Recent contracts',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.w800,
                            ),
                      ),
                      TextButton(onPressed: _refresh, child: const Text('Refresh')),
                    ],
                  ),
                  if (_contracts.isEmpty)
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          children: [
                            const Icon(Icons.description_outlined, size: 38, color: teal),
                            const SizedBox(height: 12),
                            const Text(
                              'Your contract space is ready',
                              style: TextStyle(fontWeight: FontWeight.w700),
                            ),
                            const SizedBox(height: 6),
                            const Text(
                              'Upload a contract you are authorized to use. The first classifier is a baseline, not validated LegalBERT.',
                              textAlign: TextAlign.center,
                              style: TextStyle(color: Colors.black54),
                            ),
                            const SizedBox(height: 12),
                            OutlinedButton.icon(
                              onPressed: _upload,
                              icon: const Icon(Icons.upload_file),
                              label: const Text('Choose a contract'),
                            ),
                          ],
                        ),
                      ),
                    )
                  else
                    ..._contracts.take(15).map(
                      (contract) => _ContractTile(
                        contract: contract,
                        onTap: () => _openContract(contract),
                      ),
                    ),
                  const SizedBox(height: 15),
                  const _SafetyNotice(),
                ],
              ),
      ),
    );
  }
}

class _UploadMetadata {
  const _UploadMetadata({
    required this.type,
    required this.state,
    required this.governingLaw,
    required this.msmeSupplier,
  });

  final String type;
  final String state;
  final String governingLaw;
  final bool msmeSupplier;
}

class _UploadDialog extends StatefulWidget {
  const _UploadDialog();

  @override
  State<_UploadDialog> createState() => _UploadDialogState();
}

class _UploadDialogState extends State<_UploadDialog> {
  final _governingLaw = TextEditingController();
  String _type = 'nda';
  String _state = '';
  bool _msmeSupplier = false;

  @override
  void dispose() {
    _governingLaw.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Contract details'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            DropdownButtonFormField<String>(
              value: _type,
              decoration: const InputDecoration(labelText: 'Agreement type'),
              items: _contractTypes.entries
                  .map(
                    (entry) => DropdownMenuItem<String>(
                      value: entry.key,
                      child: Text(entry.value),
                    ),
                  )
                  .toList(),
              onChanged: (value) => setState(() => _type = value ?? 'nda'),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _state,
              decoration: const InputDecoration(labelText: 'State / execution location'),
              items: [
                const DropdownMenuItem<String>(
                  value: '',
                  child: Text('Not provided'),
                ),
                ..._indianJurisdictions.map(
                  (place) => DropdownMenuItem<String>(
                    value: place,
                    child: Text(place),
                  ),
                ),
              ],
              onChanged: (value) => setState(() => _state = value ?? ''),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _governingLaw,
              decoration: const InputDecoration(labelText: 'Governing law (optional)'),
            ),
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              value: _msmeSupplier,
              onChanged: (value) => setState(() => _msmeSupplier = value ?? false),
              title: const Text(
                'Supplier may be eligible MSE',
                style: TextStyle(fontSize: 12),
              ),
              subtitle: const Text(
                'Enables a conditional MSMED review prompt. Confirm eligibility separately.',
                style: TextStyle(fontSize: 10),
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: () => Navigator.pop(
            context,
            _UploadMetadata(
              type: _type,
              state: _state,
              governingLaw: _governingLaw.text.trim(),
              msmeSupplier: _msmeSupplier,
            ),
          ),
          child: const Text('Continue'),
        ),
      ],
    );
  }
}

class ContractDetailScreen extends ConsumerStatefulWidget {
  const ContractDetailScreen({
    super.key,
    required this.contract,
    required this.result,
  });

  final Map<String, dynamic> contract;
  final Map<String, dynamic> result;

  @override
  ConsumerState<ContractDetailScreen> createState() => _ContractDetailScreenState();
}

class _ContractDetailScreenState extends ConsumerState<ContractDetailScreen> {
  late Map<String, dynamic> _result;
  bool _refreshing = false;

  @override
  void initState() {
    super.initState();
    _result = widget.result;
  }

  Future<void> _reanalyze() async {
    setState(() => _refreshing = true);
    try {
      final data = await ref.read(apiProvider).analyze(widget.contract['id'].toString());
      if (mounted) setState(() => _result = _asMap(data['result']));
    } catch (error) {
      if (mounted) _showSnack(context, friendlyError(error), error: true);
    } finally {
      if (mounted) setState(() => _refreshing = false);
    }
  }

  Future<void> _requestSuggestion(Map<String, dynamic> clause) async {
    try {
      final data = await ref.read(apiProvider).suggest(
            widget.contract['id'].toString(),
            clause['id'].toString(),
          );
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: Text('${data['category']} review prompt'),
          content: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(data['suggestion']?.toString() ?? ''),
                const SizedBox(height: 14),
                Text(
                  'Source clause: ${clause['id']} · page ${clause['page'] ?? 1}',
                  style: const TextStyle(fontSize: 11, color: teal),
                ),
                const SizedBox(height: 8),
                Text(
                  data['disclaimer']?.toString() ?? 'Review with a qualified lawyer.',
                  style: const TextStyle(fontSize: 11, color: Colors.black54),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ],
        ),
      );
    } catch (error) {
      if (mounted) _showSnack(context, friendlyError(error), error: true);
    }
  }

  Future<void> _downloadReport() async {
    try {
      final bytes = await ref.read(apiProvider).report(widget.contract['id'].toString());
      final base = (widget.contract['filename']?.toString() ?? 'contract')
          .replaceAll(RegExp(r'[^A-Za-z0-9_-]+'), '_');
      await FileSaver.instance.saveFile(
        name: 'ContractSense_${base}_report',
        bytes: bytes,
        ext: 'pdf',
        mimeType: MimeType.pdf,
      );
      if (mounted) _showSnack(context, 'PDF report saved.');
    } catch (error) {
      if (mounted) _showSnack(context, friendlyError(error), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final clauses = _asMapList(_result['clauses']);
    final checks = _asMapList(_result['legal_checks']);
    final score = (_result['overall_risk_score'] ?? 0).toString();
    final level = (_result['overall_risk_level'] ?? 'low').toString();

    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.contract['filename']?.toString() ?? 'Contract review',
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        actions: [
          IconButton(
            onPressed: _downloadReport,
            icon: const Icon(Icons.picture_as_pdf_outlined),
            tooltip: 'Save PDF report',
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _reanalyze,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 30),
          children: [
            Card(
              color: ink,
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Row(
                  children: [
                    Container(
                      width: 84,
                      height: 84,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(color: Colors.white30, width: 7),
                      ),
                      child: Text(
                        score,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 28,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                    const SizedBox(width: 18),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'REVIEW PRIORITY · NOT A LEGAL VERDICT',
                            style: TextStyle(
                              color: Color(0xFF9ED4C7),
                              fontSize: 10,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          const SizedBox(height: 7),
                          Text(
                            '${level.toUpperCase()} priority',
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w800,
                              fontSize: 20,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            '${_result['clause_count'] ?? 0} clauses · ${checks.length} review prompts',
                            style: const TextStyle(color: Colors.white70, fontSize: 12),
                          ),
                          const SizedBox(height: 7),
                          const Text(
                            'The score is a prioritization indicator, not a probability.',
                            style: TextStyle(color: Colors.white60, fontSize: 10),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Opening text excerpt',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w800,
                          ),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'First readable sentences from extracted text; not an AI-generated summary.',
                      style: TextStyle(fontSize: 11, color: Colors.black54),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _result['summary']?.toString() ?? 'No extracted text available.',
                      style: const TextStyle(height: 1.5),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      _result['disclaimer']?.toString() ?? '',
                      style: const TextStyle(fontSize: 10, color: Colors.black54),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 18),
            Text(
              'Legal review prompts',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
            ),
            const SizedBox(height: 8),
            if (checks.isEmpty)
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(15),
                  child: Text('No configured prompt triggered. This is not legal clearance.'),
                ),
              )
            else
              ...checks.map((item) => _LegalCheckCard(check: item)),
            const SizedBox(height: 18),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Clauses',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                TextButton(
                  onPressed: _refreshing ? null : _reanalyze,
                  child: _refreshing
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text('Re-run'),
                ),
              ],
            ),
            if (clauses.isEmpty)
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Text('No clauses extracted.'),
                ),
              ),
            ...clauses.map(
              (clause) => _ClauseCard(
                clause: clause,
                onSuggest: () => _requestSuggestion(clause),
              ),
            ),
            const SizedBox(height: 12),
            Card(
              color: const Color(0xFFFFF6E8),
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Text(
                  _asStringList(_result['coverage_notes']).join('\n\n'),
                  style: const TextStyle(
                    color: Color(0xFF755D35),
                    fontSize: 11,
                    height: 1.45,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => ChatScreen(contract: widget.contract),
                ),
              ),
              icon: const Icon(Icons.chat_bubble_outline),
              label: const Text('Ask about this contract'),
            ),
          ],
        ),
      ),
    );
  }
}

class _LegalCheckCard extends StatelessWidget {
  const _LegalCheckCard({required this.check});

  final Map<String, dynamic> check;

  @override
  Widget build(BuildContext context) {
    final sourceUrls = _asStringList(check['source_urls']);
    if (sourceUrls.isEmpty && check['source_url'] is String) {
      sourceUrls.add(check['source_url'] as String);
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Padding(
                  padding: EdgeInsets.only(right: 10, top: 1),
                  child: Icon(Icons.info_outline, color: teal, size: 19),
                ),
                Expanded(
                  child: Text(
                    check['rule_id']?.toString() ?? 'Review prompt',
                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
                  ),
                ),
                _RiskChip(level: check['severity']?.toString() ?? 'low'),
              ],
            ),
            const SizedBox(height: 7),
            Text(
              '${check['law'] ?? ''} · ${check['provision'] ?? ''}',
              style: const TextStyle(fontSize: 11, color: Colors.black54),
            ),
            const SizedBox(height: 7),
            Text(
              check['message']?.toString() ?? '',
              style: const TextStyle(fontSize: 12, height: 1.45),
            ),
            if (check['source_checked_on'] != null &&
                check['source_checked_on'].toString().isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                'Source checked: ${check['source_checked_on']}',
                style: const TextStyle(fontSize: 10, color: Colors.black45),
              ),
            ],
            if (sourceUrls.isNotEmpty)
              Wrap(
                spacing: 4,
                children: [
                  for (var i = 0; i < sourceUrls.length; i++)
                    TextButton.icon(
                      onPressed: () => _openSource(context, sourceUrls[i]),
                      icon: const Icon(Icons.open_in_new, size: 14),
                      label: Text(i == 0 ? 'Open official/source page' : 'Additional source'),
                    ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key, required this.contract});

  final Map<String, dynamic> contract;

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _input = TextEditingController();
  final _scrollController = ScrollController();
  List<Map<String, dynamic>> _messages = [];
  bool _loading = true;
  bool _sending = false;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  @override
  void dispose() {
    _input.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _loadHistory() async {
    try {
      _messages = await ref.read(apiProvider).chatHistory(widget.contract['id'].toString());
    } catch (error) {
      if (mounted) _showSnack(context, friendlyError(error), error: true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _send() async {
    final message = _input.text.trim();
    if (message.isEmpty || _sending) return;
    _input.clear();
    setState(() => _sending = true);
    try {
      final response = await ref.read(apiProvider).ask(
            widget.contract['id'].toString(),
            message,
          );
      if (!mounted) return;
      setState(() {
        _messages = [
          ..._messages,
          {'role': 'user', 'content': message, 'evidence': <dynamic>[]},
          {
            'role': 'assistant',
            'content': response['answer'],
            'evidence': response['evidence'] ?? <dynamic>[],
            'legal_sources': response['legal_sources'] ?? <dynamic>[],
            'provider': response['provider'] ?? '',
            'limitations': response['limitations'] ?? '',
          },
        ];
      });
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scrollController.hasClients) {
          _scrollController.animateTo(
            _scrollController.position.maxScrollExtent,
            duration: const Duration(milliseconds: 180),
            curve: Curves.easeOut,
          );
        }
      });
    } catch (error) {
      if (mounted) _showSnack(context, friendlyError(error), error: true);
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          'Ask about ${widget.contract['filename'] ?? 'contract'}',
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _messages.isEmpty
                    ? const Center(
                        child: Padding(
                          padding: EdgeInsets.all(28),
                          child: Text(
                            'Ask a question about an analyzed clause. Answers use retrieved contract evidence and configured review sources.',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: Colors.black54),
                          ),
                        ),
                      )
                    : ListView.builder(
                        controller: _scrollController,
                        padding: const EdgeInsets.all(14),
                        itemCount: _messages.length,
                        itemBuilder: (context, index) => _ChatBubble(
                          message: _messages[index],
                        ),
                      ),
          ),
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _input,
                      onSubmitted: (_) => _send(),
                      maxLines: 1,
                      decoration: const InputDecoration(
                        hintText: 'Ask about this contract…',
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    onPressed: _sending ? null : _send,
                    tooltip: 'Send question',
                    icon: _sending
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.arrow_upward),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ChatBubble extends StatelessWidget {
  const _ChatBubble({required this.message});

  final Map<String, dynamic> message;

  @override
  Widget build(BuildContext context) {
    final isUser = message['role'] == 'user';
    final evidence = _asMapList(message['evidence']);
    final legalSources = _asMapList(message['legal_sources']);
    final provider = message['provider']?.toString() ?? '';
    final limitations = message['limitations']?.toString() ?? '';
    final providerLabel = switch (provider) {
      'evidence_only_fallback' => 'EVIDENCE-ONLY · NO LLM',
      'gemini' => 'AI-GENERATED · GEMINI',
      'groq' => 'AI-GENERATED · GROQ',
      'ollama' => 'AI-GENERATED · OLLAMA',
      '' => 'CONTRACTSENSE',
      _ => provider.toUpperCase(),
    };

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 360),
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(13),
        decoration: BoxDecoration(
          color: isUser ? const Color(0xFFE6F3ED) : Colors.white,
          border: Border.all(color: const Color(0xFFE6ECE9)),
          borderRadius: BorderRadius.circular(13),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              isUser ? 'YOU' : providerLabel,
              style: const TextStyle(
                fontSize: 9,
                fontWeight: FontWeight.w800,
                color: teal,
              ),
            ),
            const SizedBox(height: 5),
            SelectableText(
              message['content']?.toString() ?? '',
              style: const TextStyle(fontSize: 12, height: 1.5),
            ),
            if (!isUser && limitations.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                limitations,
                style: const TextStyle(fontSize: 9, color: Colors.black54),
              ),
            ],
            if (evidence.isNotEmpty) ...[
              const SizedBox(height: 8),
              Wrap(
                spacing: 4,
                runSpacing: 4,
                children: evidence
                    .map(
                      (item) => Chip(
                        label: Text(
                          '${item['clause_id'] ?? 'Clause'} · p.${item['page'] ?? '?'}',
                          style: const TextStyle(fontSize: 9),
                        ),
                        visualDensity: VisualDensity.compact,
                      ),
                    )
                    .toList(),
              ),
            ],
            if (legalSources.isNotEmpty) ...[
              const Divider(height: 18),
              const Text(
                'Related legal review sources',
                style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700),
              ),
              for (final source in legalSources.take(4))
                TextButton.icon(
                  onPressed: () => _openSource(context, source['source_url']?.toString() ?? ''),
                  icon: const Icon(Icons.open_in_new, size: 13),
                  label: Text(
                    source['source_title']?.toString() ?? source['law']?.toString() ?? 'Source',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 10),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ClauseCard extends StatelessWidget {
  const _ClauseCard({required this.clause, required this.onSuggest});

  final Map<String, dynamic> clause;
  final VoidCallback onSuggest;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ExpansionTile(
        title: Row(
          children: [
            Expanded(
              child: Text(
                clause['category']?.toString() ?? 'Other',
                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
              ),
            ),
            _RiskChip(level: clause['risk_level']?.toString() ?? 'low'),
          ],
        ),
        subtitle: Text(
          'Page ${clause['page'] ?? 1} · ${clause['id'] ?? ''}',
          style: const TextStyle(fontSize: 10),
        ),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 14),
        children: [
          Align(
            alignment: Alignment.centerLeft,
            child: SelectableText(
              clause['text']?.toString() ?? '',
              style: const TextStyle(fontSize: 12, height: 1.5),
            ),
          ),
          Align(
            alignment: Alignment.centerRight,
            child: TextButton.icon(
              onPressed: onSuggest,
              icon: const Icon(Icons.edit_note),
              label: const Text('Review wording'),
            ),
          ),
        ],
      ),
    );
  }
}

class _RiskChip extends StatelessWidget {
  const _RiskChip({required this.level});

  final String level;

  @override
  Widget build(BuildContext context) {
    final color = switch (level.toLowerCase()) {
      'high' => const Color(0xFFB84D42),
      'medium' => const Color(0xFFA06B21),
      _ => const Color(0xFF438565),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
      decoration: BoxDecoration(
        color: color.withOpacity(.1),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        level.toUpperCase(),
        style: TextStyle(color: color, fontSize: 9, fontWeight: FontWeight.w800),
      ),
    );
  }
}

class _ContractTile extends StatelessWidget {
  const _ContractTile({required this.contract, required this.onTap});

  final Map<String, dynamic> contract;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final level = contract['overall_risk_level']?.toString() ?? '';
    final jurisdiction = contract['jurisdiction_state']?.toString() ?? '';
    final location = jurisdiction.isEmpty ? 'State not provided' : jurisdiction;
    return Card(
      child: ListTile(
        onTap: onTap,
        leading: const CircleAvatar(
          backgroundColor: Color(0xFFE7F3ED),
          child: Icon(Icons.description_outlined, color: teal),
        ),
        title: Text(
          contract['filename']?.toString() ?? 'Contract',
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
        ),
        subtitle: Text(
          '${_contractTypes[contract['contract_type']] ?? 'Other'} · $location · ${_date(contract['created_at'])}',
          style: const TextStyle(fontSize: 10),
        ),
        trailing: level.isEmpty ? const Icon(Icons.chevron_right) : _RiskChip(level: level),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({required this.label, required this.value, required this.icon});

  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final width = (MediaQuery.sizeOf(context).width - 48) / 2;
    return SizedBox(
      width: width,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, color: teal, size: 19),
              const SizedBox(height: 9),
              Text(
                value,
                style: const TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.w800,
                  color: ink,
                ),
              ),
              Text(label, style: const TextStyle(fontSize: 10, color: Colors.black54)),
            ],
          ),
        ),
      ),
    );
  }
}

class _SafetyNotice extends StatelessWidget {
  const _SafetyNotice();

  @override
  Widget build(BuildContext context) {
    return Card(
      color: const Color(0xFFFFF6E8),
      child: const Padding(
        padding: EdgeInsets.all(14),
        child: Text(
          'ContractSense is a decision-support prototype, not legal advice. Pan-India state-specific coverage is incomplete. Verify the cited clause and consult a qualified lawyer.',
          style: TextStyle(
            fontSize: 11,
            height: 1.45,
            color: Color(0xFF735C35),
          ),
        ),
      ),
    );
  }
}

class _Brand extends StatelessWidget {
  const _Brand();

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 30,
          height: 30,
          alignment: Alignment.center,
          decoration: const BoxDecoration(
            color: teal,
            borderRadius: BorderRadius.all(Radius.circular(9)),
          ),
          child: const Text(
            'C',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800),
          ),
        ),
        const SizedBox(width: 9),
        const Text(
          'ContractSense',
          style: TextStyle(
            fontWeight: FontWeight.w800,
            letterSpacing: -.5,
            color: ink,
          ),
        ),
      ],
    );
  }
}

Map<String, dynamic> _asMap(dynamic value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  return <String, dynamic>{};
}

List<Map<String, dynamic>> _asMapList(dynamic value) {
  if (value is! List) return <Map<String, dynamic>>[];
  return value.whereType<Map>().map((item) => Map<String, dynamic>.from(item)).toList();
}

List<String> _asStringList(dynamic value) {
  if (value is! List) return <String>[];
  return value.map((item) => item.toString()).toList();
}

String _date(dynamic value) {
  try {
    return DateFormat.yMMMd().format(DateTime.parse(value.toString()).toLocal());
  } catch (_) {
    return '';
  }
}

Future<void> _openSource(BuildContext context, String url) async {
  final uri = Uri.tryParse(url);
  if (uri == null || !uri.hasScheme) {
    _showSnack(context, 'No valid source URL is available.', error: true);
    return;
  }
  try {
    final opened = await launchUrl(uri, mode: LaunchMode.externalApplication);
    if (!opened && context.mounted) {
      _showSnack(context, 'Could not open the source link.', error: true);
    }
  } catch (_) {
    if (context.mounted) _showSnack(context, 'Could not open the source link.', error: true);
  }
}

void _showSnack(BuildContext context, String message, {bool error = false}) {
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text(message),
      backgroundColor: error ? const Color(0xFF9F483D) : const Color(0xFF286F5E),
    ),
  );
}
