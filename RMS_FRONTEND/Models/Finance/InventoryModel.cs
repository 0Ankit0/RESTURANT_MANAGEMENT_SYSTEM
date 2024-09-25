using RMS_FRONTEND.Models.Users;
using System.ComponentModel.DataAnnotations;
using System.Data;

namespace RMS_FRONTEND.Models.Finance
{
    public class InventoryModel
    {
        public int? InventoryId { get; set; }
        [MaxLength(150)]
        public string ItemName { get; set; }
        public decimal Quantity { get; set; }
        public string Unit { get; set; }
        public string? GUID { get; set; }
        public bool IsValidUnit()
        {
            return Enum.TryParse<WeightUnitEnum>(Unit, out _);
        }

    }
    public enum WeightUnitEnum
    {
        Pcs,
        Kg
    }

}
