namespace RMS_API.Models.Users
{
	public class UserRole
	{
		public int UkId { get; set; }
		public int UserRoleId { get; set; }
		public int UserId { get; set; }
		public int RoleId { get; set; }
		public string GUID { get; set; }

		public UserMaster User { get; set; }
		public RoleMaster Role { get; set; }
	}
}
