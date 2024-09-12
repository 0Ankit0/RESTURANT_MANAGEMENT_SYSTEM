using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace RMS_FRONTEND.Data.Finance
{
    public class Inventory
    {
        [Key]
        public int InventoryId { get; set; }
        public string ItemName { get; set; }
        [Column(TypeName = "decimal(18, 2)")]
        public decimal Quantity { get; set; }
        public string Unit { get; set; }
        public string GUID { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime? UpdatedAt { get; set; }
       
        public ICollection<Recipe> Recipes { get; set; } // Navigation property
    }
}
