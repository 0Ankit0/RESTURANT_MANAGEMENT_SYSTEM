﻿using Swashbuckle.AspNetCore.Annotations;
using System.ComponentModel.DataAnnotations;

namespace RMS_API.Models
{
    public class LoginModel
    {
        [Required(ErrorMessage = "Please enter your username or email address")]
        [StringLength(50, ErrorMessage = "Username or email cannot be longer than 50 characters")]
        [SwaggerSchema(Description ="The email or username of the user")]
        public string UsernameOrEmail { get; set; }

        [Required(ErrorMessage = "Please enter your password")]
        [DataType(DataType.Password)]
        [SwaggerSchema(Description ="Password for the provided user name or email")]
        public string Password { get; set; }

      
    }

    public class userModel
    {
        [Required(ErrorMessage = "Please enter your username")]
        [StringLength(50, ErrorMessage = "Username cannot be longer than 50 characters")]
        public string Username { get; set; }

        [Required(ErrorMessage = "Please enter your email address")]
        [EmailAddress(ErrorMessage = "Please enter a valid email address")]
        public string Email { get; set; }

        [Required(ErrorMessage = "Please enter your password")]
        [DataType(DataType.Password)]
        [MinLength(6, ErrorMessage = "Password must be at least 6 characters")]
        [RegularExpression(@"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$",
            ErrorMessage = "Password must be at least 6 characters long and contain at least one uppercase letter, one lowercase letter, one number, and one special character.")]
        public string Password { get; set; }

        [Required(ErrorMessage = "Please confirm your password")]
        [Compare("Password", ErrorMessage = "The password and confirmation password do not match")]
        [DataType(DataType.Password)]
        public string ConfirmPassword { get; set; }

        [Phone(ErrorMessage = "Please enter a valid phone number")]
        [DataType(DataType.PhoneNumber)]
        public string PhoneNumber { get; set; }


    }
}
