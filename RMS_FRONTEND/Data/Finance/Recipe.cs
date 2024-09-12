using RMS_FRONTEND.Data.Menu;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace RMS_FRONTEND.Data.Finance
{
    public class Recipe
    {
        [Key]
        public int RecipeId { get; set; }
        public int? MenuId { get; set; }
        public int? InventoryId { get; set; }
        [Column(TypeName = "decimal(18, 2)")]
        public decimal QuantityRequired { get; set; }
        public string GUID { get; set; }

        [ForeignKey("MenuId")]
        public MenuMaster Menu { get; set; } // Navigation property
        [ForeignKey("InventoryId")]
        public Inventory Inventory { get; set; } // Navigation property
    }
}
