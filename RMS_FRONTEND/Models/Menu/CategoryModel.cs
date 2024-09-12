using RMS_FRONTEND.Models.Orders;
using System.ComponentModel.DataAnnotations;

namespace RMS_FRONTEND.Models.Menu
{
    public class CategoryModel
    {
        public int CategoryId { get; set; }
        [MaxLength(150)]
        public string CategoryName { get; set; }
        public string GUID { get; set; }
        public bool Active { get; set; }

        public ICollection<MenuModel> Menu { get; set; }

    }
}
