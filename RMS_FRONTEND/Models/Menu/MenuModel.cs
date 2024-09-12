using RMS_FRONTEND.Models.Finance;
using RMS_FRONTEND.Models.Orders;

namespace RMS_FRONTEND.Models.Menu
{
    public class MenuModel
    {
        public int MenuId { get; set; }
        public string MenuName { get; set; }
        public string Description { get; set; }
        public decimal Price { get; set; }
        public int? CategoryId { get; set; }
        public bool IsAvailable { get; set; }
        public string GUID { get; set; }
        public bool Active { get; set; }

    }
}
