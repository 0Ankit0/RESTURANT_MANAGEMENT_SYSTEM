namespace RMS_FRONTEND.Models.Users
{
    public class UserRoleModel
    {
        public int UserRoleId { get; set; }
        public int? UserId { get; set; }
        public int? RoleId { get; set; }
        public string GUID { get; set; }
    }
}
