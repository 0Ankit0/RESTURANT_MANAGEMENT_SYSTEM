using RMS_API.Data.Finance;
using RMS_API.Data.Orders;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace RMS_API.Data.Menu
{
    public class MenuMaster
    {
        [Key]
        public int MenuId { get; set; }
        [MaxLength(150)]
        public string MenuName { get; set; }
        public string Description { get; set; }
        [Column(TypeName = "decimal(18, 2)")]
        public decimal Price { get; set; }
        public int? CategoryId { get; set; }
        public bool IsAvailable { get; set; }
        public string GUID { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime? UpdatedAt { get; set; }
        public bool Active { get; set; }

        [ForeignKey("CategoryId")]
        public CategoryMaster Category { get; set; } // Navigation property
        public ICollection<Recipe> Recipes { get; set; } // Navigation property
        public ICollection<OrderDetails> OrderDetails { get; set; } // Navigation property
    }
}
