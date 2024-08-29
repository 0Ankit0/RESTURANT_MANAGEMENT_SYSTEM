namespace RMS_API.Models.Users
{
	public class RoleMaster
	{
		public int UkId { get; set; }
		public int RoleId { get; set; }
		public string RoleName { get; set; }
		public string GUID { get; set; }
		public DateTime CreatedAt { get; set; }
		public DateTime? UpdatedAt { get; set; }
		public bool? Active { get; set; }

		public ICollection<UserMaster> Users { get; set; }
		public ICollection<UserRole> UserRoles { get; set; }
	}
}
