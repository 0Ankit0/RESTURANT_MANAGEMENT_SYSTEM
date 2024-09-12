using RMS_FRONTEND.Data.Users;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace RMS_FRONTEND.Data.Orders
{
    public class OrderMaster
    {
        [Key]
        public int OrderId { get; set; }
        public int TableNumber { get; set; }
        public int? WaiterId { get; set; }
        public string OrderStatus { get; set; }
        public DateTime OrderDate { get; set; }
        public DateTime? UpdatedAt { get; set; }

        public ICollection<OrderDetails> OrderDetails { get; set; } // Navigation property
        [ForeignKey("WaiterId")]
        public UserMaster Waiter { get; set; } // Navigation property, assuming User entity exists
    }
}
