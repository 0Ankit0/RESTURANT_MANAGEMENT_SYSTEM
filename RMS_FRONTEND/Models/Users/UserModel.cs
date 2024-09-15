using System.ComponentModel;
using System.ComponentModel.DataAnnotations;

namespace RMS_FRONTEND.Models.Users
{
    public class UserModel
    {
        public int UserId { get; set; }
		[Required(ErrorMessage = "User name is required.")]
		public string UserName { get; set; }


		[Required(ErrorMessage = "Email is required.")]
		[EmailAddress(ErrorMessage = "Invalid email address.")]
        public string UserEmail { get; set; }


		[Required(ErrorMessage = "Password is required.")]
		[DataType(DataType.Password)]
        [Display(Name = "Password")]
        [RegularExpression(@"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\da-zA-Z]).{8,}$", ErrorMessage = "Password must be greater than 8 characters and contain at least one uppercase letter, one lowercase letter, one digit, and one special character.")]
        public string Password { get; set; }


        [Compare("Password", ErrorMessage = "The password and confirmation password do not match.")]
		[Required(ErrorMessage = "Confirm password is required.")]
        [DataType(DataType.Password)]
		public string ConfirmPassword { get; set; }

        
        public string? Address { get; set; }


		[DataType(DataType.PhoneNumber)]
        [Phone(ErrorMessage = "Invalid phone number.")]
        public string? Phone { get; set; }
        public string? Role { get; set; }
        public string? GUID { get; set; }

        public bool IsValidRole()
        {
            return Enum.TryParse<RoleEnum>(Role, out _);
        }
    }
    public enum RoleEnum
    {
        Admin,
        Waiter,
        Cook,
        Cashier
    }
}
