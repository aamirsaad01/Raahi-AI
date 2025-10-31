import pandas as pd
import json
from datetime import datetime
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChecklistGenerator:
    def __init__(self, location_csv_path='E:/Raahi-AI/backend_scripts/data/location_mapping.csv'):
        """Initialize the checklist generator with location data"""
        self.locations_df = pd.read_csv(location_csv_path)
        self.checklist_rules = self._initialize_rules()
    
    def _initialize_rules(self) -> Dict:
        """Define packing rules based on various conditions"""
        return {
            # Base essentials (always needed)
            "essentials": {
                "items": [
                    "CNIC/Passport",
                    "Travel permits (if required)",
                    "Cash (ATMs may be limited)",
                    "Mobile phone + charger",
                    "Power bank",
                    "First aid kit",
                    "Personal medications",
                    "Water bottle",
                    "Sunglasses",
                    "Sunscreen (SPF 50+)",
                    "Lip balm",
                    "Toiletries",
                    "Hand sanitizer",
                    "Tissues/wet wipes"
                ]
            },
            
            # Climate-based clothing
            "climate_gear": {
                "alpine": {
                    "items": [
                        "Heavy winter jacket",
                        "Thermal innerwear (top + bottom)",
                        "Wool sweaters",
                        "Fleece jacket",
                        "Waterproof pants",
                        "Insulated gloves",
                        "Warm socks (3-4 pairs)",
                        "Winter cap/beanie",
                        "Scarf/neck warmer",
                        "Snow boots (waterproof)",
                        "Gaiters"
                    ]
                },
                "temperate": {
                    "items": [
                        "Light jacket/windbreaker",
                        "Sweater/hoodie",
                        "Long pants",
                        "Light gloves",
                        "Warm socks",
                        "Cap/hat",
                        "Comfortable walking shoes",
                        "Rain jacket"
                    ]
                },
                "subtropical": {
                    "items": [
                        "Light jacket (for evenings)",
                        "T-shirts",
                        "Light pants/jeans",
                        "Comfortable shoes",
                        "Hat/cap for sun"
                    ]
                },
                "warm": {
                    "items": [
                        "Light cotton clothes",
                        "T-shirts",
                        "Shorts/light pants",
                        "Sandals",
                        "Hat for sun protection",
                        "Light jacket (optional)"
                    ]
                }
            },
            
            # Season-specific items
            "seasonal": {
                "winter": {  # Dec, Jan, Feb
                    "months": [12, 1, 2],
                    "items": [
                        "Extra warm layers",
                        "Hand warmers",
                        "Moisturizer (for dry skin)",
                        "Thermos flask"
                    ]
                },
                "spring": {  # Mar, Apr, May
                    "months": [3, 4, 5],
                    "items": [
                        "Light rain jacket",
                        "Umbrella",
                        "Allergy medication (if prone)"
                    ]
                },
                "summer": {  # Jun, Jul, Aug
                    "months": [6, 7, 8],
                    "items": [
                        "Extra sunscreen",
                        "Insect repellent",
                        "Light breathable clothes",
                        "Cooling towel"
                    ]
                },
                "autumn": {  # Sep, Oct, Nov
                    "months": [9, 10, 11],
                    "items": [
                        "Light jacket",
                        "Layering clothes",
                        "Umbrella"
                    ]
                }
            },
            
            # Activity-specific gear
            "activities": {
                "hiking": {
                    "items": [
                        "Hiking boots (broken in)",
                        "Trekking poles",
                        "Backpack (30-40L)",
                        "Trail map/GPS device",
                        "Headlamp/flashlight",
                        "Energy bars/snacks",
                        "Electrolyte powder",
                        "Blister patches",
                        "Emergency whistle",
                        "Multi-tool/knife",
                        "Waterproof bag covers",
                        "Extra batteries"
                    ]
                },
                "skiing": {
                    "items": [
                        "Ski jacket",
                        "Ski pants",
                        "Ski goggles",
                        "Helmet",
                        "Ski gloves (waterproof)",
                        "Base layers (moisture-wicking)",
                        "Neck gaiter/balaclava",
                        "Hand/toe warmers",
                        "Ski socks",
                        "Sunscreen (high SPF)"
                    ],
                    "note": "Ski equipment can be rented at most resorts"
                },
                "roadtrip": {
                    "items": [
                        "Vehicle documents",
                        "Spare tire + jack",
                        "Emergency triangle",
                        "Jumper cables",
                        "Basic tool kit",
                        "Car charger",
                        "Roadside assistance number",
                        "Cooler box",
                        "Travel pillow",
                        "Entertainment (music/audiobooks)",
                        "Garbage bags"
                    ]
                },
                "city_tour": {
                    "items": [
                        "Comfortable walking shoes",
                        "Day backpack",
                        "City map/guidebook",
                        "Camera",
                        "Portable charger",
                        "Light jacket",
                        "Reusable shopping bag",
                        "Local currency"
                    ]
                },
                "camping": {
                    "items": [
                        "Tent",
                        "Sleeping bag (appropriate rating)",
                        "Sleeping pad/mattress",
                        "Camping stove + fuel",
                        "Cooking utensils",
                        "Matches/lighter (waterproof)",
                        "Headlamp + extra batteries",
                        "Rope/paracord",
                        "Tarp/groundsheet",
                        "Camping chairs (optional)",
                        "Biodegradable soap",
                        "Trash bags",
                        "Water purification tablets"
                    ]
                },
                "photography": {
                    "items": [
                        "Camera + lenses",
                        "Extra memory cards",
                        "Extra batteries",
                        "Camera cleaning kit",
                        "Tripod",
                        "Lens filters (polarizing, ND)",
                        "Camera bag (weatherproof)",
                        "Lens cloth",
                        "Remote shutter release",
                        "Rain cover for camera"
                    ]
                },
                "cultural": {
                    "items": [
                        "Modest clothing (local customs)",
                        "Scarf/shawl (for religious sites)",
                        "Comfortable shoes (temple visits)",
                        "Small donation money",
                        "Guidebook/cultural info",
                        "Notebook for experiences"
                    ]
                }
            },
            
            # Elevation-based items
            "elevation": {
                "high_altitude": {  # > 2500m
                    "threshold": 2500,
                    "items": [
                        "Altitude sickness medication",
                        "Extra water (stay hydrated)",
                        "High-energy snacks",
                        "Warm layers (temperature drops)",
                        "Lip balm with SPF"
                    ]
                }
            },
            
            # Regional specific items
            "regional": {
                "Gilgit-Baltistan": {
                    "items": [
                        "Extra cash (limited ATMs)",
                        "Downloaded maps (limited connectivity)",
                        "Warm clothes (even in summer)",
                        "Local SIM card info"
                    ]
                },
                "KPK Highlands": {
                    "items": [
                        "Permits for restricted areas",
                        "Local guide contact (recommended)",
                        "Warm layers"
                    ]
                },
                "Hazara Division": {
                    "items": [
                        "Rain gear (prone to rain)",
                        "Warm clothes for high areas"
                    ]
                },
                "Murree & Galyat": {
                    "items": [
                        "Umbrella (frequent rain)",
                        "Light warm clothes"
                    ]
                }
            }
        }
    
    def get_season(self, month: int) -> str:
        """Determine season from month number"""
        for season, data in self.checklist_rules["seasonal"].items():
            if month in data["months"]:
                return season
        return "spring"  # default
    
    def get_location_info(self, area_name: str, region_name: Optional[str] = None) -> Optional[Dict]:
        """Get location information from database"""
        query = self.locations_df['city'].str.lower() == area_name.lower()
        if region_name:
            query = query & (self.locations_df['parent_region'] == region_name)
        
        result = self.locations_df[query]
        
        if result.empty:
            logger.warning(f"Location '{area_name}' not found in database")
            return None
        
        return result.iloc[0].to_dict()
    
    def generate_checklist(
        self,
        area: str,
        region: Optional[str],
        month: int,
        activities: List[str]
    ) -> Dict:
        """
        Generate personalized packing checklist
        
        Args:
            area: Name of the destination area
            region: Parent region (optional)
            month: Travel month (1-12)
            activities: List of planned activities
        
        Returns:
            Dictionary containing checklist and metadata
        """
        # Get location data
        location_info = self.get_location_info(area, region)
        
        if not location_info:
            return {
                "success": False,
                "error": f"Location '{area}' not found in database",
                "suggestion": "Please check the spelling or try a different location"
            }
        
        # Initialize checklist
        checklist = {
            "destination": {
                "area": location_info['city'],
                "region": location_info['parent_region'],
                "elevation": location_info['elevation'],
                "climate_zone": location_info['climate_zone'],
                "best_season": location_info['tourist_season']
            },
            "travel_info": {
                "month": month,
                "season": self.get_season(month)
            },
            "activities": activities,
            "items": {}
        }
        
        # Collect items
        all_items = []
        
        # 1. Add essentials (always needed)
        all_items.extend(self.checklist_rules["essentials"]["items"])
        checklist["items"]["Essentials"] = self.checklist_rules["essentials"]["items"]
        
        # 2. Add climate-appropriate clothing
        climate_zone = location_info['climate_zone']
        if climate_zone in self.checklist_rules["climate_gear"]:
            climate_items = self.checklist_rules["climate_gear"][climate_zone]["items"]
            all_items.extend(climate_items)
            checklist["items"]["Climate Gear"] = climate_items
        
        # 3. Add seasonal items
        season = self.get_season(month)
        season_items = self.checklist_rules["seasonal"][season]["items"]
        all_items.extend(season_items)
        checklist["items"]["Seasonal Items"] = season_items
        
        # 4. Add activity-specific gear
        activity_items = {}
        for activity in activities:
            activity_lower = activity.lower()
            if activity_lower in self.checklist_rules["activities"]:
                items = self.checklist_rules["activities"][activity_lower]["items"]
                all_items.extend(items)
                activity_items[activity.title()] = items
        
        if activity_items:
            checklist["items"]["Activity Gear"] = activity_items
        
        # 5. Add elevation-based items
        elevation = location_info['elevation']
        if elevation and elevation > 2500:
            altitude_items = self.checklist_rules["elevation"]["high_altitude"]["items"]
            all_items.extend(altitude_items)
            checklist["items"]["High Altitude"] = altitude_items
        
        # 6. Add regional specific items
        region_name = location_info['parent_region']
        if region_name in self.checklist_rules["regional"]:
            regional_items = self.checklist_rules["regional"][region_name]["items"]
            all_items.extend(regional_items)
            checklist["items"]["Regional Specifics"] = regional_items
        
        # Add warnings and tips
        checklist["warnings"] = self._generate_warnings(location_info, month, activities)
        checklist["tips"] = self._generate_tips(location_info, month, activities)
        
        checklist["success"] = True
        checklist["total_items"] = len(set(all_items))  # Remove duplicates for count
        
        return checklist
    
    def _generate_warnings(self, location_info: Dict, month: int, activities: List[str]) -> List[str]:
        """Generate warnings based on conditions"""
        warnings = []
        
        # Elevation warning
        if location_info['elevation'] and location_info['elevation'] > 2500:
            warnings.append("⚠️ High altitude area - acclimatize properly and watch for altitude sickness symptoms")
        
        # Winter travel
        if month in [12, 1, 2]:
            warnings.append("❄️ Winter travel - roads may be blocked by snow, check conditions before travel")
        
        # Remote area
        if location_info['parent_region'] == "Gilgit-Baltistan":
            warnings.append("📶 Limited mobile connectivity - download offline maps and inform family")
        
        # Skiing specific
        if "skiing" in [a.lower() for a in activities]:
            warnings.append("⛷️ Check avalanche warnings and ski with proper safety equipment")
        
        return warnings
    
    def _generate_tips(self, location_info: Dict, month: int, activities: List[str]) -> List[str]:
        """Generate helpful tips"""
        tips = []
        
        # Best season tip
        tips.append(f"🌟 Best time to visit: {location_info['tourist_season']}")
        
        # Photography tip
        if "photography" in [a.lower() for a in activities]:
            tips.append("📸 Golden hour (sunrise/sunset) offers the best lighting for mountain photography")
        
        # Hiking tip
        if "hiking" in [a.lower() for a in activities]:
            tips.append("🥾 Start hikes early in the morning to avoid afternoon weather changes")
        
        # General tip
        tips.append("💡 Pack layers - mountain weather can change quickly")
        
        return tips


# CLI Testing Interface
def cli_test():
    """Command-line interface for testing"""
    print("="*60)
    print("🎒 RAAHI AI - Packing Checklist Generator")
    print("="*60)
    
    generator = ChecklistGenerator('E:/Raahi-AI/backend_scripts/data/location_mapping.csv')
    
    # Get available regions
    regions = generator.locations_df['parent_region'].unique()
    print("\nAvailable Regions:")
    for i, region in enumerate(regions, 1):
        print(f"{i}. {region}")
    
    # Get user input
    region_idx = int(input("\nSelect region (number): ")) - 1
    selected_region = regions[region_idx]
    
    # Get areas in selected region
    areas = generator.locations_df[
        generator.locations_df['parent_region'] == selected_region
    ]['city'].values
    
    print(f"\nAvailable areas in {selected_region}:")
    for i, area in enumerate(areas[:20], 1):  # Show first 20
        print(f"{i}. {area}")
    if len(areas) > 20:
        print(f"... and {len(areas) - 20} more")
    
    area_name = input("\nEnter area name: ")
    
    # Get month
    month = int(input("Enter travel month (1-12): "))
    
    # Get activities
    print("\nAvailable activities:")
    activities_list = ["hiking", "skiing", "roadtrip", "city_tour", "camping", "photography", "cultural"]
    for i, activity in enumerate(activities_list, 1):
        print(f"{i}. {activity}")
    
    activity_input = input("\nSelect activities (comma-separated numbers, e.g., 1,3,6): ")
    selected_activities = [activities_list[int(i)-1] for i in activity_input.split(',')]
    
    # Generate checklist
    print("\n" + "="*60)
    print("Generating your personalized checklist...")
    print("="*60 + "\n")
    
    result = generator.generate_checklist(
        area=area_name,
        region=selected_region,
        month=month,
        activities=selected_activities
    )
    
    if result.get("success"):
        print_checklist(result)
    else:
        print(f"❌ Error: {result.get('error')}")
        print(f"💡 {result.get('suggestion', '')}")


def print_checklist(checklist: Dict):
    """Pretty print the checklist"""
    dest = checklist["destination"]
    
    print(f"📍 Destination: {dest['area']}, {dest['region']}")
    print(f"🏔️ Elevation: {dest['elevation']}m")
    print(f"🌡️ Climate: {dest['climate_zone'].title()}")
    print(f"📅 Travel Month: {checklist['travel_info']['month']} ({checklist['travel_info']['season'].title()})")
    print(f"🎯 Activities: {', '.join(checklist['activities'])}")
    print(f"\n✅ Total Items: {checklist['total_items']}\n")
    
    # Print warnings
    if checklist.get("warnings"):
        print("⚠️  IMPORTANT WARNINGS:")
        for warning in checklist["warnings"]:
            print(f"   {warning}")
        print()
    
    # Print tips
    if checklist.get("tips"):
        print("💡 HELPFUL TIPS:")
        for tip in checklist["tips"]:
            print(f"   {tip}")
        print()
    
    # Print items by category
    print("="*60)
    print("📋 YOUR PACKING CHECKLIST")
    print("="*60)
    
    for category, items in checklist["items"].items():
        print(f"\n{category.upper()}:")
        if isinstance(items, dict):
            for subcategory, subitems in items.items():
                print(f"\n  {subcategory}:")
                for item in subitems:
                    print(f"    ☐ {item}")
        else:
            for item in items:
                print(f"  ☐ {item}")
    
    print("\n" + "="*60)
    print("Have a safe and amazing trip! 🌟")
    print("="*60)


if __name__ == "__main__":
    cli_test()