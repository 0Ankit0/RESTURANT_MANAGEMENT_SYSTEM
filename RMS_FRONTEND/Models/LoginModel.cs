using System.ComponentModel.DataAnnotations;

namespace RMS_FRONTEND.Models
{
    public class LoginModel
    {
        [Required(ErrorMessage = "Please enter your Email")]
        public string Email { get; set; }

        [Required(ErrorMessage = "Please enter your password")]
        public string Password { get; set; }
    }
}
