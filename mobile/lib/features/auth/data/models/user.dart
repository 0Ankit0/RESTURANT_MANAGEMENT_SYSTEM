class User {
  final String id;
  final String username;
  final String email;
  final bool isConfirmed;
  final bool isActive;
  final bool isSuperuser;
  final bool otpEnabled;
  final bool otpVerified;
  final String? firstName;
  final String? lastName;
  final String? phone;
  final String? imageUrl;
  final String? createdAt;
  final String? bio;
  final List<String> roles;

  const User({
    required this.id,
    required this.username,
    required this.email,
    required this.isConfirmed,
    required this.isActive,
    this.isSuperuser = false,
    this.otpEnabled = false,
    this.otpVerified = false,
    this.firstName,
    this.lastName,
    this.phone,
    this.imageUrl,
    this.createdAt,
    this.bio,
    this.roles = const [],
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'].toString(),
      username: json['username'] as String,
      email: json['email'] as String,
      isConfirmed: json['is_confirmed'] as bool? ?? false,
      isActive: json['is_active'] as bool? ?? true,
      isSuperuser: json['is_superuser'] as bool? ?? false,
      otpEnabled: json['otp_enabled'] as bool? ?? false,
      otpVerified: json['otp_verified'] as bool? ?? false,
      firstName: json['first_name'] as String?,
      lastName: json['last_name'] as String?,
      phone: json['phone'] as String?,
      imageUrl: json['image_url'] as String?,
      createdAt: json['created_at'] as String?,
      bio: json['bio'] as String?,
      roles: (json['roles'] as List<dynamic>?)?.map((e) => e as String).toList() ?? [],
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'username': username,
        'email': email,
        'is_confirmed': isConfirmed,
        'is_active': isActive,
        'is_superuser': isSuperuser,
        'otp_enabled': otpEnabled,
        'otp_verified': otpVerified,
        'first_name': firstName,
        'last_name': lastName,
        'phone': phone,
        'image_url': imageUrl,
        'created_at': createdAt,
        'bio': bio,
        'roles': roles,
      };

  String get displayName {
    if (firstName != null && lastName != null && firstName!.isNotEmpty && lastName!.isNotEmpty) {
      return '$firstName $lastName';
    }
    if (firstName != null && firstName!.isNotEmpty) return firstName!;
    return username;
  }

  String get initials {
    if (firstName != null && firstName!.isNotEmpty) {
      final last = lastName != null && lastName!.isNotEmpty ? lastName![0].toUpperCase() : '';
      return '${firstName![0].toUpperCase()}$last';
    }
    return username.isNotEmpty ? username[0].toUpperCase() : '?';
  }

  User copyWith({
    String? firstName,
    String? lastName,
    String? phone,
    String? imageUrl,
    bool? otpEnabled,
    bool? otpVerified,
    String? bio,
    List<String>? roles,
  }) {
    return User(
      id: id,
      username: username,
      email: email,
      isConfirmed: isConfirmed,
      isActive: isActive,
      isSuperuser: isSuperuser,
      otpEnabled: otpEnabled ?? this.otpEnabled,
      otpVerified: otpVerified ?? this.otpVerified,
      firstName: firstName ?? this.firstName,
      lastName: lastName ?? this.lastName,
      phone: phone ?? this.phone,
      imageUrl: imageUrl ?? this.imageUrl,
      createdAt: createdAt,
      bio: bio ?? this.bio,
      roles: roles ?? this.roles,
    );
  }
}
