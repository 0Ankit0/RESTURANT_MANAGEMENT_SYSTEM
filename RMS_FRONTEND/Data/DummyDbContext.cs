using Microsoft.EntityFrameworkCore;
using RMS_FRONTEND.Data.Users;
using RMS_FRONTEND.Data.Finance;
using RMS_FRONTEND.Data.Menu;
using RMS_FRONTEND.Data.Orders;

namespace RMS_FRONTEND.Data
{
    public class DummyDbContext : DbContext
    {
        public DummyDbContext(DbContextOptions<DummyDbContext> options)
            : base(options)
        {
        }


        public DbSet<UserMaster> UserMasters { get; set; }
        public DbSet<CategoryMaster> Categories { get; set; }
        public DbSet<MenuMaster> Menus { get; set; }
        public DbSet<Inventory> Inventories { get; set; }
        public DbSet<Recipe> Recipes { get; set; }
        public DbSet<OrderMaster> Orders { get; set; }
        public DbSet<OrderDetails> OrderDetails { get; set; }
        public DbSet<Billing> Billings { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            // Configuring RoleMaster
            
            // Configuring UserMaster
            modelBuilder.Entity<UserMaster>()
                .HasKey(u => u.UserId);

            modelBuilder.Entity<MenuMaster>()
           .HasOne(m => m.Category)
           .WithMany(c => c.Menus)
           .HasForeignKey(m => m.CategoryId);

            modelBuilder.Entity<Recipe>()
                .HasOne(r => r.Menu)
                .WithMany(m => m.Recipes)
                .HasForeignKey(r => r.MenuId);

            modelBuilder.Entity<Recipe>()
                .HasOne(r => r.Inventory)
                .WithMany(i => i.Recipes)
                .HasForeignKey(r => r.InventoryId);

            modelBuilder.Entity<OrderMaster>()
                .HasOne(o => o.Waiter) // Assuming there is a User entity for the waiter
                .WithMany()
                .HasForeignKey(o => o.WaiterId);

            modelBuilder.Entity<OrderDetails>()
                .HasOne(od => od.Order)
                .WithMany(o => o.OrderDetails)
                .HasForeignKey(od => od.OrderId);

            modelBuilder.Entity<OrderDetails>()
                .HasOne(od => od.Menu)
                .WithMany(m => m.OrderDetails)
                .HasForeignKey(od => od.MenuId);

            modelBuilder.Entity<Billing>()
                .HasOne(b => b.Order)
                .WithMany()
                .HasForeignKey(b => b.OrderId);

        }
    }


}
