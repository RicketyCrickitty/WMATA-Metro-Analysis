# Mapping of WMATA Station IDs to Common Names
# This allows us to link the Rail Data (IDs) to the Bus Data (Names/Locations)

STATION_ID_TO_NAME = {
    'A01': 'Metro Center',
    'A02': 'Farragut North',
    'A03': 'Dupont Circle',
    'A04': 'Woodley Park',
    'A05': 'Cleveland Park',
    'A06': 'Van Ness',
    'A07': 'Tenleytown',
    'A08': 'Friendship Heights',
    'A09': 'Bethesda',
    'A10': 'Medical Center',
    'A11': 'Grosvenor',
    'A12': 'North Bethesda',
    'A13': 'Twinbrook',
    'A14': 'Rockville',
    'A15': 'Shady Grove',
    'B01': 'Gallery Place',
    'B02': 'Judiciary Square',
    'B03': 'Union Station',
    'B04': 'Rhode Island Ave',
    'B05': 'Brookland',
    'B06': 'Fort Totten',
    'B07': 'Takoma',
    'B08': 'Silver Spring',
    'B09': 'Forest Glen',
    'B10': 'Wheaton',
    'B11': 'Glenmont',
    'C01': 'Metro Center',
    'C02': 'McPherson Square',
    'C03': 'Farragut West',
    'C04': 'Foggy Bottom',
    'C05': 'Rosslyn',
    'C06': 'Arlington Cemetery',
    'C07': 'Pentagon',
    'C08': 'Pentagon City',
    'C09': 'Crystal City',
    'C10': 'Ronald Reagan Washington National Airport',
    'C11': 'Potomac Yard', 
    'C12': 'Braddock Road',
    'C13': 'King St-Old Town',
    'C14': 'Eisenhower Avenue',
    'C15': 'Huntington',
    'D01': 'Federal Triangle',
    'D02': 'Smithsonian',
    'D03': 'L\'Enfant Plaza',
    'D04': 'Federal Center SW',
    'D05': 'Capitol South',
    'D06': 'Eastern Market',
    'D07': 'Potomac Ave',
    'D08': 'Stadium-Armory',
    'D09': 'Minnesota Ave',
    'D10': 'Deanwood',
    'D11': 'Cheverly',
    'D12': 'Landover',
    'D13': 'New Carrollton',
    'E01': 'Mt Vernon Sq',
    'E02': 'Shaw-Howard U',
    'E03': 'U Street',
    'E04': 'Columbia Heights',
    'E05': 'Georgia Ave-Petworth',
    'E06': 'Fort Totten',
    'E07': 'West Hyattsville',
    'E08': 'Hyattsville Crossing',
    'E09': 'College Park',
    'E10': 'Greenbelt',
    'F01': 'Gallery Place',
    'F02': 'Archives',
    'F03': 'L\'Enfant Plaza',
    'F04': 'Waterfront',
    'F05': 'Navy Yard',
    'F06': 'Anacostia',
    'F07': 'Congress Heights',
    'F08': 'Southern Avenue',
    'F09': 'Naylor Road',
    'F10': 'Suitland',
    'F11': 'Branch Ave',
    'G01': 'Benning Road',
    'G02': 'Capitol Heights',
    'G03': 'Addison Road',
    'G04': 'Morgan Boulevard',
    'G05': 'Downtown Largo',
    'J02': 'Van Dorn Street',
    'J03': 'Franconia-Springfield',
    'K01': 'Court House',
    'K02': 'Clarendon',
    'K03': 'Virginia Square',
    'K04': 'Ballston',
    'K05': 'East Falls Church',
    'K06': 'West Falls Church',
    'K07': 'Dunn Loring',
    'K08': 'Vienna',
    'N01': 'McLean',
    'N02': 'Tysons',
    'N03': 'Greensboro',
    'N04': 'Spring Hill',
    'N06': 'Wiehle-Reston East',
    'N07': 'Reston Town Center',
    'N08': 'Herndon',
    'N09': 'Innovation Center',
    'N10': 'Dulles Airport',
    'N11': 'Loudoun Gateway',
    'N12': 'Ashburn'
}

# Ordered lists of stations for drawing the lines
RAIL_LINES = {
    'Red': {
        'color': '#BE2D25', # WMATA Red
        'stations': ['A15','A14','A13','A12','A11','A10','A09','A08','A07','A06','A05','A04','A03','A02','A01','B01','B02','B03','B04','B05','B06','B07','B08','B09','B10','B11']
    },
    'Blue': {
        'color': '#0075BF', # WMATA Blue
        'stations': ['J03','J02','C13','C12','C11','C10','C09','C08','C07','C06','C05','C04','C03','C02','C01','D01','D02','D03','D04','D05','D06','D07','D08','G01','G02','G03','G04','G05']
    },
    'Orange': {
        'color': '#E87515', # WMATA Orange
        'stations': ['K08','K07','K06','K05','K04','K03','K02','K01','C05','C04','C03','C02','C01','D01','D02','D03','D04','D05','D06','D07','D08','D09','D10','D11','D12','D13']
    },
    'Silver': {
        'color': '#97999B', # WMATA Silver
        'stations': ['N12','N11','N10','N09','N08','N07','N06','N04','N03','N02','N01','K05','K04','K03','K02','K01','C05','C04','C03','C02','C01','D01','D02','D03','D04','D05','D06','D07','D08','G01','G02','G03','G04','G05']
    },
    'Green': {
        'color': '#00A94F', # WMATA Green
        'stations': ['F11','F10','F09','F08','F07','F06','F05','F04','F03','F02','F01','E01','E02','E03','E04','E05','E06','E07','E08','E09','E10']
    },
    'Yellow': {
        'color': '#FCDD44', # WMATA Yellow
        'stations': ['C15','C14','C13','C12','C11','C10','C09','C08','C07','F03','F02','F01','E01']
    }
}