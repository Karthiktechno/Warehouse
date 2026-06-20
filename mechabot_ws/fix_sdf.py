import os
import re

def fix_world(path):
    with open(path, "r") as f:
        content = f.read()

    pattern = re.compile(
        r'<model\s+name=[\'"]([^\'"]+)[\'"]>\s*'
        r'<include>\s*'
        r'<uri>([^<]+)</uri>\s*'
        r'</include>\s*'
        r'<pose\s*[^>]*>([^<]+)</pose>\s*'
        r'</model>',
        re.MULTILINE
    )

    def repl(m):
        name = m.group(1)
        uri = m.group(2)
        pose = m.group(3)
        return f'<include>\n      <name>{name}</name>\n      <uri>{uri}</uri>\n      <pose>{pose}</pose>\n    </include>'

    new_content = pattern.sub(repl, content)

    # There might be some without pose or pose in different order.
    # Let's do a more robust replacement using BeautifulSoup or regex
    
    with open(path, "w") as f:
        f.write(new_content)
    
    print(f"Fixed {path}")

import glob
for world in glob.glob("/home/karthik/Mech Bot/mechabot_ws/src/mechabot_description/worlds/*.world"):
    fix_world(world)
