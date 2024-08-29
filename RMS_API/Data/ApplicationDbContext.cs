using Microsoft.EntityFrameworkCore;
using RMS_API.Models.Users;
using System.Xml;

namespace RMS_API.Data
{
	public class ApplicationDbContext : DbContext
	{
		public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
			: base(options)
		{
		}

		public DbSet<RoleMaster> RoleMasters { get; set; }
		public DbSet<UserMaster> UserMasters { get; set; }
		public DbSet<UserRole> UserRoles { get; set; }
		protected override void OnModelCreating(ModelBuilder modelBuilder)
		{
			// Configuring RoleMaster
			modelBuilder.Entity<RoleMaster>()
				.HasKey(r => r.RoleId);

			modelBuilder.Entity<RoleMaster>()
				.HasMany(r => r.Users) // Corrected
				.WithOne(u => u.Role)
				.HasForeignKey(u => u.RoleId);

			modelBuilder.Entity<RoleMaster>()
				.HasMany(r => r.UserRoles)
				.WithOne(ur => ur.Role)
				.HasForeignKey(ur => ur.RoleId);

			// Configuring UserMaster
			modelBuilder.Entity<UserMaster>()
				.HasKey(u => u.UserId);

			modelBuilder.Entity<UserMaster>()
				.HasOne(u => u.Role)
				.WithMany(r => r.Users) // Corrected
				.HasForeignKey(u => u.RoleId);

			modelBuilder.Entity<UserMaster>()
				.HasMany(u => u.UserRoles)
				.WithOne(ur => ur.User)
				.HasForeignKey(ur => ur.UserId);

			// Configuring UserRole
			modelBuilder.Entity<UserRole>()
				.HasKey(ur => ur.UserRoleId);

			modelBuilder.Entity<UserRole>()
				.HasOne(ur => ur.User)
				.WithMany(u => u.UserRoles)
				.HasForeignKey(ur => ur.UserId);

			modelBuilder.Entity<UserRole>()
				.HasOne(ur => ur.Role)
				.WithMany(r => r.UserRoles)
				.HasForeignKey(ur => ur.RoleId);
		}


	}

}
