using System.ComponentModel.DataAnnotations;

namespace RMS_FRONTEND.Models.Finance
{
    public class InventoryModel
    {
        public int InventoryId { get; set; }
        [MaxLength(150)]
        public string ItemName { get; set; }
        public decimal Quantity { get; set; }
        public string Unit { get; set; }
        public string GUID { get; set; }

     }
}
