using System.ComponentModel.DataAnnotations;

namespace RMS_API.Data.Menu
{
    public class CategoryMaster
    {
        [Key]
        public int CategoryId { get; set; }
        [MaxLength(150)]
        public string CategoryName { get; set; }
        public string GUID { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime? UpdatedAt { get; set; }
        public bool Active { get; set; }

        public ICollection<MenuMaster> Menus { get; set; } // Navigation property
    }
}
