using System.ComponentModel.DataAnnotations;

namespace RMS_API.Data.Users
{
    public class UserRole
    {
        public UserRole()
        {
            GUID = Guid.NewGuid().ToString();
        }
        [Key]
        public int UserRoleId { get; set; }
        public int? UserId { get; set; }
        public int? RoleId { get; set; }
        public string GUID { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime? UpdatedAt { get; set; }
        public bool Active { get; set; } = true;

        public UserMaster User { get; set; }
        public RoleMaster Role { get; set; }
    }
}
