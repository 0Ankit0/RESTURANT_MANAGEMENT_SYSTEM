using RMS_FRONTEND.Data.Orders;

namespace RMS_FRONTEND.Models.Orders
{
    public class OrderModel
    {
        public int? OrderId { get; set; }
        public int TableNumber { get; set; }
        public int? WaiterId { get; set; }
        public string? OrderStatus { get; set; }
        public decimal? TotalPrice { get; set; }
        public List<OrderDetailsModel> OrderDetails { get; set; }
    }
}
