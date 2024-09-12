
using RMS_FRONTEND.Data.Orders;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace RMS_FRONTEND.Data.Finance
{
    public class Billing
    {
        [Key]
        public int BillingId { get; set; }
        public int? OrderId { get; set; }
        [Column(TypeName = "decimal(18, 2)")]
        public decimal TotalAmount { get; set; }
        public DateTime BillingDate { get; set; }
        public bool Paid { get; set; }

        [ForeignKey("OrderId")]
        public OrderMaster Order { get; set; } // Navigation property
    }
}
