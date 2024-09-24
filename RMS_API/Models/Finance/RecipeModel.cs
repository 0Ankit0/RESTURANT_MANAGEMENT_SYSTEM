using RMS_API.Models.Menu;
using System.ComponentModel.DataAnnotations.Schema;

namespace RMS_API.Models.Finance
{
    public class RecipeModel
    {
        public int? RecipeId { get; set; }
        public int? MenuId { get; set; }
        public int? InventoryId { get; set; }
        [Column(TypeName = "decimal(18, 2)")]
        public decimal QuantityRequired { get; set; }
        public string? GUID { get; set; }

     }
    public class RecipeModelWithMenu 
    {
        public int? MenuId { get; set; }
        public required List<RecipeModel> Recipes { get; set; }
    }
}
