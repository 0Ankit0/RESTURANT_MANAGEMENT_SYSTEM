using RMS_API.Models.Menu;

namespace RMS_API.Models.Orders
{
    public class OrderDetailsModel
    {
        public int? OrderDetailId { get; set; }
        public int? OrderId { get; set; }
        public int MenuId { get; set; }
        public int Quantity { get; set; }
        public decimal? Price { get; set; }

    }
    public class OrderDetailsData
    {
        public int? OrderDetailId { get; set; }
        public int? OrderId { get; set; }
        public string Menu { get; set; }
        public int Quantity { get; set; }
        public decimal? Price { get; set; }

    }
}
