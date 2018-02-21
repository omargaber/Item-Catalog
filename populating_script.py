from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base, Items

engine = create_engine('sqlite:///itemcatalog.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

categories = ['Soccer', 'Basketball', 'Baseball', 'Snowboarding', 'Hockey']


# Soccer Items
# Retrieved from: https://www.completesoccerguide.com/soccer-equipment/
soccer_items = {
    'Footwear': 'Soccer players should play in turf shoes or cleats, special footwear made exclusively for soccer',
    'Soccer Socks': 'Soccer socks are extremely long. They cover shin-guards.',
    'Shin-Guards':'Shin-guards protect player shin, a vulnerable part of a player body that often gets kicked.',
    'Soccer Ball': 'Some coaches provide soccer balls, but purchasing one is highly recommended.',
    'Water Bottle': 'Every player needs to drink water during games and practices.',
    }
# Basketball Items
# Retreived from: https://sportsaspire.com/list-of-basketball-equipment-with-pictures
basketball_items = {
    'Basketball': 'For practicing, one can play with a rubber ball. For professional competitions, one needs to use an inflated ball made of leather.',
    'Shoes': 'These shoes are specially designed to maintain high traction on the basketball court.',
    'Basketball Shooting Equipment': 'The hoop or basket is a horizontal metallic rim, circular in shape. This rim is attached to a net.',
    'Backboard': 'The backboard is the rectangular board that is placed behind the rim.',
    'Whistle':'The coach or referee uses a whistle to indicate the start or end of a game.'
}

# Baseball Items
# Retreived from: https://en.wikipedia.org/wiki/Baseball_clothing_and_equipment
baseball_items = {
    'Bat':'A rounded, solid wooden or hollow aluminum bat.',
    'Ball':'A cork sphere, tightly wound with layers of yarn or string and covered with a stitched leather coat.',
    'Base':'One of four corners of the infield which must be touched by a runner in order to score a run',
    'Glove':'Leather gloves worn by players in the field.',
    'Batting gloves':'Gloves often worn on one or both hands by the batter.'
}

# Snowboarding Items
# Retreived from: https://en.wikipedia.org/wiki/Snowboard#Boots
snowboarding_items = {
    'Snowboard':'Boards where both feet are secured to the same board and are wider than skis,',
    'Boots':'Snowboard boots are mostly considered soft boots, though alpine snowboarding uses a harder boot similar to a ski boot.',
    'Bindings':'Bindings are separate components from the snowboard deck and are very important parts of the total snowboard interface.'
}

#Hockey Items
# Retreived from: https://en.wikipedia.org/wiki/Ice_hockey_equipment
hockey_items = {
    'Helmet':'A helmet with strap, and optionally a face cage or visor, is required of all ice hockey players.',
    'Neck guard':'For "skaters", a neck guard typically consists of a series of nylon or ABS plates for puncture resistance.',
    'Shoulder pads':'Hockey shoulder pads are typically composed of a passed vest with front and back panels.'
}

#Adding Categories and items to DB
for cat in categories:
    category_name = Category(name=cat)
    session.add(category_name)
    session.commit()
    if cat == "Soccer":
        for soccerItem in soccer_items:
            item = Items(name=soccerItem, description=soccer_items[soccerItem], category = category_name)
            session.add(item)
            session.commit()
    elif cat == "Basketball":
        for basketballItem in basketball_items:
            item = Items(name=basketballItem, description=basketball_items[basketballItem], category = category_name)
            session.add(item)
            session.commit()
    elif cat == "Baseball":
        for baseballItem in baseball_items:
            item = Items(name=baseballItem, description=baseball_items[baseballItem], category = category_name)
            session.add(item)
            session.commit()
    elif cat == "Snowboarding":
        for snowbItem in snowboarding_items:
            item = Items(name=snowbItem, description=snowboarding_items[snowbItem], category = category_name)
            session.add(item)
            session.commit()
    elif cat == "Hockey":
        for hockeyItem in hockey_items:
            item = Items(name=hockeyItem, description = hockey_items[hockeyItem], category = category_name)
            session.add(item)
            session.commit()

print "Database Populated!"