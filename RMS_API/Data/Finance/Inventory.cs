using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace RMS_API.Data.Finance
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

    public class InventoryTransaction
    {
        [Key]
        public int TransactionId { get; set; }
        public int InventoryId { get; set; }
        public DateTime TransactionDate { get; set; }
        [Column(TypeName = "decimal(18, 2)")]
        public decimal Quantity { get; set; }
        public TransactionType TransactionType { get; set; } // e.g., "Addition", "Subtraction", "Adjustment"
        public string Description { get; set; }

        [ForeignKey("InventoryId")]
        public Inventory Inventory { get; set; } // Navigation property
    }
    public enum TransactionType
    {
        Addition,
        Subtraction,
        Adjustment
    }
}
