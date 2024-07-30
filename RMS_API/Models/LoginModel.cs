using System.ComponentModel.DataAnnotations;

namespace RMS_API.Models
{
    public class LoginModel
    {
        public string TokenNo { get; set; }

        public string GUID { get; set; }

        [Required(ErrorMessage = "Please enter your Email")]
        [DataType(DataType.EmailAddress)]
        public string Email { get; set; }

        [Required(ErrorMessage = "Please enter your password")]
        [DataType(DataType.Password)]
        public string Password { get; set; }

    }
}
