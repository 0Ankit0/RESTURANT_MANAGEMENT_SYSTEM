using RMS_FRONTEND.Models.Menu;

namespace RMS_FRONTEND.Models.Orders
{
    public class OrderDetailsModel
    {
        public int OrderDetailId { get; set; }
        public int? OrderId { get; set; }
        public int? MenuId { get; set; }
        public int Quantity { get; set; }
        public decimal Price { get; set; }

    }
}
