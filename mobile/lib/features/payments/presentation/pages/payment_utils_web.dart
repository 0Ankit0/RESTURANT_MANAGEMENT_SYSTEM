// Web implementation — uses package:web (dart:js_interop) to POST the eSewa form.
import 'package:web/web.dart' as web;

Future<void> submitEsewaFormWeb(
    String formAction, Map<String, dynamic> fields) async {
  final form = web.HTMLFormElement();
  form.method = 'POST';
  form.action = formAction;

  fields.forEach((key, value) {
    final input = web.HTMLInputElement();
    input.type = 'hidden';
    input.name = key;
    input.value = value.toString();
    form.append(input);
  });

  web.document.body!.append(form);
  form.submit();
}
