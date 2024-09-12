using RMS_FRONTEND.Models.Orders;

namespace RMS_FRONTEND.Models.Finance
{
    public class BillingModel
    {
        public int BillingId { get; set; }
        public int? OrderId { get; set; }
        public decimal TotalAmount { get; set; }
        public bool Paid { get; set; }

        public List<OrderDetailsModel> OrderDetails { get; set; }
    }
}
