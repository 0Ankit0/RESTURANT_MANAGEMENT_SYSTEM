class RegisterRequest {
  final String username;
  final String email;
  final String password;
  final String confirmPassword;
  final String? firstName;
  final String? lastName;
  final String? phone;

  const RegisterRequest({
    required this.username,
    required this.email,
    required this.password,
    required this.confirmPassword,
    this.firstName,
    this.lastName,
    this.phone,
  });

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{
      'username': username,
      'email': email,
      'password': password,
      'confirm_password': confirmPassword,
    };
    if (firstName != null) map['first_name'] = firstName;
    if (lastName != null) map['last_name'] = lastName;
    if (phone != null) map['phone'] = phone;
    return map;
  }
}
