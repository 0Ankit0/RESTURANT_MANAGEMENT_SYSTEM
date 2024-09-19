namespace RMS_API.Models.Users
{
    public class UserModel
    {
        public int UserId { get; set; }
        public string UserName { get; set; }
        public string UserEmail { get; set; }
        public string? Password { get; set; }
        public string? Address { get; set; }
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
