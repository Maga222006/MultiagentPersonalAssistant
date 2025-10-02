from langchain.tools import tool
from tuya_iot import TuyaOpenAPI
import phonenumbers
import pycountry
import os

endpoint_map = {
    "https://openapi.tuyacn.com": [86],
    "https://openapi.tuyain.com": [91],
    "https://openapi.tuyaus.com": [1, 51, 52, 54, 55, 56, 57, 58, 81, 82, 239,
                                   245, 502, 591, 593, 595, 597, 598, 674, 678, 682, 683, 685, 686, 690, 970,
                                   1340, 1684, 1670, 1671, 1787, 1809, 1829, 1849, 5999, 35818, 64],
    "https://openapi.tuyaeu.com": [7, 20, 27, 30, 31, 32, 33, 34, 36, 39, 40,
                                   90, 92, 93, 94, 212, 213, 216, 218, 220, 221, 222, 223, 224, 225, 226, 227,
                                   228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 240, 241, 242, 243,
                                   244, 246, 248, 250, 251, 252, 253, 254, 255, 256, 257, 258, 260, 261, 262,
                                   263, 264, 265, 266, 267, 268, 269, 291, 297, 298, 299, 350, 351, 352, 353,
                                   354, 355, 356, 357, 358, 359, 370, 371, 372, 373, 374, 375, 376, 377, 378,
                                   379, 380, 381, 382, 385, 386, 387, 389, 420, 421, 423, 500, 501, 503, 504,
                                   505, 506, 507, 508, 509, 590, 592, 594, 596, 672, 676, 679, 680, 681, 687,
                                   688, 689, 691, 692, 960, 961, 962, 964, 965, 966, 967, 968, 971, 972, 973,
                                   974, 975, 976, 977, 992, 993, 994, 995, 996, 998, 1242, 1246, 1264, 1268,
                                   1284, 1345, 1441, 1473, 1649, 1664, 1721, 1758, 1767, 1784, 1868, 1869,
                                   1876, 4779, 61, 880, 41, 43, 44, 45, 46, 47, 48, 49],
    "https://openapi-sg.iotbing.com": [84, 856, 855, 66, 95, 60, 65, 62, 63,
                                       673, 670, 675, 677, 852, 853, 886],
}
country = pycountry.countries.lookup(os.getenv('TUYA_COUNTRY').title())
country_code = phonenumbers.country_code_for_region(country.alpha_2)
for endpoint, country_codes in endpoint_map.items():
    if country_code in country_codes:
        os.environ['TUYA_COUNTRY_CODE'] = str(country_code)
        os.environ['TUYA_ENDPOINT'] = endpoint
        break
openapi = TuyaOpenAPI(os.getenv('TUYA_ENDPOINT'), os.getenv('TUYA_ACCESS_ID'), os.getenv('TUYA_ACCESS_KEY'))
connection = openapi.connect(os.getenv('TUYA_USERNAME'), os.getenv('TUYA_PASSWORD'), os.getenv('TUYA_COUNTRY_CODE'), 'TuyaSmart')
if not connection['success']:
    connection = openapi.connect(os.getenv('TUYA_USERNAME'), os.getenv('TUYA_PASSWORD'), os.getenv('TUYA_COUNTRY_CODE'), 'SmartLife')

def get_device_list():
    """List all the smart home devices."""
    try:
        response = openapi.get('/v1.0/users/{}/devices'.format(connection['result']['uid']))['result']
        devices = []
        for device in response:
            devices.append({"id": device['id'], 'name': device['name'], 'states': device['status']})
        return "\n\n".join(f"{i + 1}. {device['name']} (id: {device['id']})\nStates:\n" + "\n".join(f"{state}" for state in device['states']) for i, device in enumerate(devices))
    except Exception as e:
        return None

@tool
def change_device_states(id:str, commands:list[dict]):
    """
    Control the smart home devices by sending commands.
    Accepts device id:str and a list of commands: List[dict].
    Commands is a list of changed device states.
    State format: {'code': ..., 'value': ...}
    """
    response = openapi.post('/v1.0/devices/{}/commands'.format(id), {"commands": commands})
    return "success" if response["success"] else "failure"