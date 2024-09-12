using RMS_FRONTEND.Data.Menu;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace RMS_FRONTEND.Data.Orders
{
    public class OrderDetails
    {
        [Key]
        public int OrderDetailId { get; set; }
        public int? OrderId { get; set; }
        public int? MenuId { get; set; }
        public int Quantity { get; set; }
        [Column(TypeName = "decimal(18, 2)")]
        public decimal Price { get; set; }

        [ForeignKey("OrderId")]
        public OrderMaster Order { get; set; } // Navigation property
        [ForeignKey("MenuId")]
        public MenuMaster Menu { get; set; } // Navigation property
    }
}
