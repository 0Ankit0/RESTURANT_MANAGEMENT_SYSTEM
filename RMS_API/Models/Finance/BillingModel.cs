using RMS_API.Models.Orders;

namespace RMS_API.Models.Finance
{
    public class BillingModel
    {
        public int? BillingId { get; set; }
        public DateTime BillingDate { get; set; }
        public int? OrderId { get; set; }
        public decimal TotalAmount { get; set; }
        public bool Paid { get; set; }

        public List<OrderDetailsModel>? OrderDetails { get; set; }
    }
    public class BillingData
    {
        public int? BillingId { get; set; }
        public DateTime BillingDate { get; set; }
        public int? OrderId { get; set; }
        public decimal TotalAmount { get; set; }
        public bool Paid { get; set; }

        public List<OrderDetailsData>? OrderDetails { get; set; }
    }
}
