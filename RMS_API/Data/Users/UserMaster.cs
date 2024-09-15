using System.ComponentModel.DataAnnotations;

namespace RMS_API.Data.Users
{
    public class UserMaster
    {
        public UserMaster()
        {
            GUID = Guid.NewGuid().ToString();
        }
        public int UserId { get; set; }
        public string UserName { get; set; }
        public string UserEmail { get; set; }
        public string Password { get; set; }
        public string? Address { get; set; }
        public string? Phone { get; set; }
        public string GUID { get; set; }
		public string? Role { get; set; }
		public DateTime CreatedAt { get; set; }
        public DateTime? UpdatedAt { get; set; }
        public bool Active { get; set; } = true;

    }
    public enum RoleEnum
    {
        Admin,
        Waiter,
        Cook,
        Cashier
    }
}
