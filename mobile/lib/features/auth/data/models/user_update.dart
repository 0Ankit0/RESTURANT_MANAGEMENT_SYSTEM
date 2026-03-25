class UserUpdate {
  final String? email;
  final String? firstName;
  final String? lastName;
  final String? phone;
  final String? password;

  const UserUpdate({this.email, this.firstName, this.lastName, this.phone, this.password});

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{};
    if (email != null) map['email'] = email;
    if (firstName != null) map['first_name'] = firstName;
    if (lastName != null) map['last_name'] = lastName;
    if (phone != null) map['phone'] = phone;
    if (password != null) map['password'] = password;
    return map;
  }
}
