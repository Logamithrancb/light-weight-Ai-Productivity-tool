import os
import random
import csv

# Set random seed for reproducibility
random.seed(42)

# Entities for template filling
SUBJECTS = ["Math", "Physics", "Chemistry", "Biology", "History", "Computer Science", "Economics", "Literature", "Art History", "Calculus"]
TOPICS = ["quantum physics", "organic synthesis", "cell division", "industrial revolution", "neural networks", "macroeconomics", "modernism", "linear algebra", "data structures", "photosynthesis", "ancient civilization", "genetics", "thermodynamics", "compiler design", "cryptography"]
GROCERIES = ["apples", "bananas", "milk", "bread", "eggs", "chicken", "spinach", "tomatoes", "cheese", "coffee", "cereal", "yogurt", "avocado", "orange juice", "pasta"]
GADGETS = ["phone", "headphones", "smartwatch", "keyboard", "mouse", "monitor", "charger", "laptop", "tablet", "speaker", "external hard drive"]
ITEMS = ["toilet paper", "batteries", "light bulbs", "shampoo", "toothpaste", "laundry detergent", "hand sanitizer", "soap", "trash bags", "dishwashing liquid"]
NAMES = ["John", "Sarah", "Alex", "Emily", "Michael", "David", "Jessica", "Daniel", "Chris", "Sophia", "Olivia", "James", "Emma", "Liam", "Isabella"]
DEPTS = ["marketing", "engineering", "sales", "product", "design", "operations", "HR", "QA", "finance", "legal"]
CLIENTS = ["Acme Corp", "Globex", "Initech", "Umbrella Corp", "Stark Industries", "Wayne Enterprises", "Hooli", "Soylent Corp"]
SYSTEMS = ["auth", "payment", "database", "ui", "notification", "billing", "dashboard", "analytics", "search engine", "user profile"]
PROJECTS = ["Alpha", "Apollo", "Phoenix", "Titan", "Vanguard", "Genesis", "Orion", "Falcon", "Nebula", "Helix"]
MEDICINES = ["Aspirin", "Ibuprofen", "Amoxicillin", "Metformin", "Lisinopril", "Lipitor", "Vitamins", "Allergy pills", "Eye drops"]
PLACES = ["San Francisco", "New York", "Lake Tahoe", "Yosemite", "Paris", "London", "Tokyo", "Rome", "Chicago", "Boston"]
INSTRUMENTS = ["guitar", "piano", "violin", "flute", "drums", "saxophone", "ukulele"]
HOBBY_IDEAS = ["woodworking", "gardening", "photography", "baking sourdough", "learning Spanish", "sketching", "origami", "home brewing", "pottery"]
SERVICES = ["Netflix", "Spotify", "Amazon Prime", "GitHub", "Gym Membership", "Adobe Creative Cloud", "Dropbox", "Slack", "Zoom"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
MONEY = ["$10", "$15", "$50", "$100", "$250", "$500", "$1000", "$1200"]
STOCKS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "NFLX", "META"]
TIMES = ["9:00 AM", "2:30 PM", "5:00 PM", "8:00 PM", "noon", "midnight", "10:30 AM", "4:15 PM"]
DATES = ["tomorrow", "next Monday", "Friday", "June 30th", "July 5th", "next week", "in 3 days", "this weekend", "tonight", "at 9 PM"]
BPS = ["120/80", "118/75", "125/82", "115/78", "122/79"]
WEIGHTS = ["68", "72", "75", "80", "65", "70", "85"]
CONCEPTS = ["energy transformation", "cell reproduction", "total GDP output", "memory allocation structures", "gradient descent", "supply and demand curves", "post-modern aesthetics", "eigenvalues and eigenvectors", "recursion algorithms", "light absorption in plants"]
NOTES = ["needs review later", "highly important for final exam", "discuss at the next standup meeting", "will double check the figures", "save for reference in future projects", "inspired by a recent podcast"]
JOURNAL_TEXTS = ["felt incredibly productive and energetic today", "completed major milestones and ran 5k", "spent too much time on distractions, need to focus tomorrow", "had a relaxing evening with friends", "finished reading a great chapter of my book"]

# Template repository per Category and Intent
# Format: (template_string, priority_class)
TEMPLATES = {
    "Study": {
        "Task": [
            ("Complete the assignment for {subject} before the deadline", "High"),
            ("Finish the {subject} project report and upload it", "Medium"),
            ("Submit the {subject} lab report", "High"),
            ("Solve the practice problems in chapter {num} of {subject}", "Medium"),
            ("Write the essay for {subject} history class", "Medium"),
            ("Prepare slides for {subject} presentation", "High"),
            ("Draft the outline for {subject} research paper", "Medium"),
            ("Format bibliography for {subject} assignment", "Low"),
            ("Revise the syllabus for {subject}", "Low"),
            ("Email the professor regarding {subject} questions", "Medium")
        ],
        "Todo": [
            ("Read pages {num} to {num} of the {subject} textbook", "Medium"),
            ("Research {topic} for the upcoming {subject} project", "Medium"),
            ("Study {subject} for {num} hours today", "Medium"),
            ("Summarize the lecture notes on {topic} for {subject}", "Medium"),
            ("Watch the tutorial video on {topic}", "Low"),
            ("Review vocabulary flashcards for {subject}", "Low"),
            ("Go over the formulas for {subject}", "Medium"),
            ("Find reference papers on {topic}", "Medium"),
            ("Listen to educational podcast about {topic}", "Low"),
            ("Brainstorm thesis statements for {subject}", "Medium")
        ],
        "Reminder": [
            ("Remember to prepare for the {subject} exam on {date}", "High"),
            ("Remind me to return the {subject} library book by {date}", "Medium"),
            ("Don't forget the group study session for {subject} at {time} on {date}", "Medium"),
            ("Set a reminder to review {subject} formulas tomorrow", "Medium"),
            ("Remind me to sign up for the {subject} workshop by {date}", "High"),
            ("Don't forget the tutorial session on {topic} at {time}", "Medium"),
            ("Remind me to ask {name} for {subject} study guides", "Low"),
            ("Set a reminder to practice {subject} problems", "Medium"),
            ("Remember to check the online gradebook tonight", "Low"),
            ("Remind me to submit the draft for {subject} next week", "High")
        ],
        "Note": [
            ("Notes from today's lecture on {topic}: {note_detail}", "Low"),
            ("Concept definition: {topic} is defined as {concept_detail}", "Low"),
            ("Useful study resource for {subject}: {url}", "Low"),
            ("Key takeaways about {topic} from the textbook", "Low"),
            ("Formula list for {subject} includes {topic} equations", "Low"),
            ("My thoughts on the reading assignment for {subject}", "Low"),
            ("Professor mentioned that {topic} will be on the final exam", "Medium"),
            ("Research question idea: how does {topic} impact modern science", "Low"),
            ("Summary of {subject} discussion board posts", "Low"),
            ("Important definitions for {subject} exam revision", "Medium")
        ]
    },
    "Work": {
        "Task": [
            ("Prepare the presentation deck for the {dept} meeting", "High"),
            ("Send the draft contract to {client} for review", "High"),
            ("Review the pull request for the {system} module", "Medium"),
            ("Fix the critical bug in the {system} pipeline", "High"),
            ("Deploy the new version of {system} to production", "High"),
            ("Update the client onboarding document for {client}", "Medium"),
            ("Schedule a kickoff meeting for Project {project}", "Medium"),
            ("Write unit tests for the {system} controllers", "Medium"),
            ("Submit the weekly progress report to the manager", "Medium"),
            ("Refactor the backend API routing files", "Medium")
        ],
        "Todo": [
            ("Brainstorm ideas for the new marketing campaign for {project}", "Medium"),
            ("Draft the email reply to {client} regarding updates", "Medium"),
            ("Update the project wiki documentation for {project}", "Low"),
            ("Schedule a quick alignment call with {name} about {topic}", "Medium"),
            ("Organize the folders in the shared drive", "Low"),
            ("Research competitor products in the {dept} space", "Low"),
            ("Review team feedback on Project {project}", "Medium"),
            ("Plan tasks for the upcoming sprint", "Medium"),
            ("Update timesheet with project codes", "Low"),
            ("Clean up the inbox and archive old emails", "Low")
        ],
        "Reminder": [
            ("Remind me of the {dept} project status meeting at {time}", "Medium"),
            ("Remember to submit timesheets before Friday {time}", "High"),
            ("Set a reminder for performance review with {name} on {date}", "High"),
            ("Don't forget to follow up with {client} regarding the proposal", "High"),
            ("Remind me to check the database logs at {time}", "Medium"),
            ("Remember to call {name} about the client contract on {date}", "Medium"),
            ("Set a reminder to review the dashboard analytics tomorrow", "Medium"),
            ("Don't forget to send the invoice to {client} next week", "High"),
            ("Remind me to backup the production databases", "High"),
            ("Set a reminder for the design sync with {name} on {date}", "Medium")
        ],
        "Note": [
            ("Meeting minutes from {dept} sync: {note_detail}", "Low"),
            ("Feedback on the design proposal: {note_detail}", "Low"),
            ("Idea for system optimization: use serverless architecture for {system}", "Low"),
            ("Worklog notes: worked on fixing the {system} latency issue today", "Low"),
            ("Client preferences for {client}: highly values speed and communication", "Low"),
            ("Notes on Project {project} timeline and milestones", "Low"),
            ("Instructions for deploying {system} code", "Medium"),
            ("Key takeaways from the tech workshop on {topic}", "Low"),
            ("Project details: {project} aims to rebuild the {system} service", "Low"),
            ("Summary of discussion with {name} about {topic}", "Low")
        ]
    },
    "Shopping": {
        "Task": [
            ("Buy {grocery} and {grocery} from the local supermarket", "Low"),
            ("Order a new {gadget} from online store", "Medium"),
            ("Pick up {grocery} and some coffee on my way home", "Low"),
            ("Purchase a nice birthday gift for {name}", "Medium"),
            ("Restock on {item} and laundry detergent", "Low"),
            ("Get new filters for the water pitcher", "Low"),
            ("Buy a pair of running shoes from the sports store", "Medium"),
            ("Order school supplies for the kids online", "Medium"),
            ("Pick up the dry cleaning from the shop", "Low"),
            ("Buy replacement bulbs for the living room lamps", "Low")
        ],
        "Todo": [
            ("Create a grocery list for the weekly meal plan", "Low"),
            ("Research prices for a {gadget} online", "Low"),
            ("Compare features of {gadget} brands", "Low"),
            ("Look for coupons or discounts on {item}", "Low"),
            ("Find out store hours for the hardware shop", "Low"),
            ("Browse online deals for {gadget} accessories", "Low"),
            ("Make a list of clothes to buy for the trip", "Low"),
            ("Check stock availability for {gadget} at the retail store", "Low"),
            ("Create wishlist for upcoming black friday sales", "Low"),
            ("Organize shopping cart items on Amazon", "Low")
        ],
        "Reminder": [
            ("Remind me to buy {grocery} when near the market", "Low"),
            ("Remember to purchase the concert tickets tonight", "High"),
            ("Set a reminder to order {item} before the sale ends", "Medium"),
            ("Don't forget to buy milk and bread on Friday", "Low"),
            ("Remind me to pick up the prescription medicine tomorrow", "High"),
            ("Set a reminder to order {item} before we run out", "Medium"),
            ("Remember to check out the grocery deals on {date}", "Low"),
            ("Remind me to buy a birthday card for {name} on {date}", "Medium"),
            ("Don't forget to order coffee beans next week", "Low"),
            ("Set a reminder to purchase anniversary flowers on {date}", "High")
        ],
        "Note": [
            ("Shopping wishlist: {gadget}, {gadget}, and a new bag", "Low"),
            ("Price details: {item} is cheaper at Walmart compared to target", "Low"),
            ("Sizes list: {name} wears shoe size 9 and shirt size M", "Low"),
            ("Shopping budget notes: maximum $200 for clothing", "Low"),
            ("Store recommendations: buy fresh vegetables at the farmer's market", "Low"),
            ("Model name for {gadget} I want to buy: Version {num}", "Low"),
            ("Gift ideas for {name}: book about {topic} or a warm scarf", "Low"),
            ("grocery inventory list: need to buy {grocery} next time", "Low"),
            ("Return policy details: returns accepted within 30 days", "Low"),
            ("Shopping list notes: check if we have enough {item} at home", "Low")
        ]
    },
    "Health": {
        "Task": [
            ("Schedule an appointment with Dr. {name} for annual checkup", "High"),
            ("Pick up my prescription medicine {medicine} from pharmacy", "High"),
            ("Refill the {medicine} supply at the local drug store", "High"),
            ("Run {num} miles on the treadmill at the gym", "Medium"),
            ("Do a strength training workout session", "Medium"),
            ("Go for a dental checkup and teeth cleaning", "High"),
            ("Register for the virtual yoga class", "Medium"),
            ("Prep healthy meals for the upcoming week", "Medium"),
            ("Drink a glass of water every hour today", "Medium"),
            ("Schedule a physical therapy session for back pain", "High")
        ],
        "Todo": [
            ("Go to the local gym for a quick cardio session", "Medium"),
            ("Drink at least {num} glasses of water today", "Medium"),
            ("Do 15 minutes of mindfulness meditation before bed", "Low"),
            ("Track daily calorie and macro intake in the app", "Low"),
            ("Stretch for 10 minutes in the morning", "Low"),
            ("Research healthy dinner recipes with spinach and chicken", "Low"),
            ("Perform deep breathing exercises for stress relief", "Low"),
            ("Take vitamins and dietary supplements", "Medium"),
            ("Log sleep duration and quality in the health app", "Low"),
            ("Read article on benefits of regular stretching", "Low")
        ],
        "Reminder": [
            ("Remind me to take my {medicine} at {time}", "High"),
            ("Remember to book the dental checkup on {date}", "High"),
            ("Set a reminder to stretch every hour at work today", "Low"),
            ("Don't forget the medical blood test tomorrow morning", "High"),
            ("Remind me to drink water before the run", "Medium"),
            ("Remember to apply eye drops at {time}", "Medium"),
            ("Set a reminder to order refills of {medicine} by {date}", "High"),
            ("Don't forget the therapy appointment with {name} at {time}", "High"),
            ("Remind me to go to bed before 11:00 PM tonight", "Medium"),
            ("Set a reminder to track steps in the evening", "Low")
        ],
        "Note": [
            ("Blood pressure reading today: {bp} mmHg", "Medium"),
            ("Weight tracking entry: {weight} kg this morning", "Low"),
            ("Notes from doctor consultation: {note_detail}", "High"),
            ("Symptom journal: felt slight headache in the afternoon", "Medium"),
            ("List of allergies: allergic to penicillin and pollen", "High"),
            ("Workout stats: ran {num} kilometers, burnt 400 calories", "Low"),
            ("Dietary note: need to reduce sugar intake and eat more fiber", "Low"),
            ("Sleep diary: slept for 7 hours, felt rested", "Low"),
            ("Health tip: drinking green tea improves metabolism", "Low"),
            ("Medical insurance policy number: {num}{num}{num}", "Medium")
        ]
    },
    "Personal": {
        "Task": [
            ("Call {name} to catch up on weekend plans", "Medium"),
            ("Clean the living room and vacuum the rugs", "Low"),
            ("Plan the weekend road trip itinerary to {place}", "Medium"),
            ("Organize the bedroom closet and donate old clothes", "Low"),
            ("Mow the lawn and trim the garden hedges", "Low"),
            ("Wash the dirty laundry and fold the sheets", "Low"),
            ("Cook dinner for the family tonight", "Medium"),
            ("Fix the leaking kitchen sink faucet", "Medium"),
            ("Send a thank you note to {name} for the gift", "Low"),
            ("Renew my passport before the travel dates", "High")
        ],
        "Todo": [
            ("Water the balcony plants and flowers", "Low"),
            ("Wash and clean the car inside and out", "Low"),
            ("Create a list of birthday gift ideas for {name}", "Low"),
            ("Practice playing the {instrument} for 30 minutes", "Low"),
            ("Draft a letter of appreciation to my friend", "Low"),
            ("Research flight tickets to {place} for vacation", "Medium"),
            ("Clean the coffee machine filter", "Low"),
            ("Read a chapter of my new fantasy book", "Low"),
            ("Organize the photo library on my laptop", "Low"),
            ("Write a journal entry about {journal_texts}", "Low")
        ],
        "Reminder": [
            ("Remind me to call {name} on their birthday next week", "Medium"),
            ("Remember to water the backyard garden tomorrow morning", "Low"),
            ("Set a reminder to pick up dry cleaning on {date}", "Medium"),
            ("Don't forget to RSVP to {name}'s dinner invitation", "Medium"),
            ("Remind me to feed the pets at {time}", "High"),
            ("Set a reminder to call my parents on Sunday afternoon", "Medium"),
            ("Remember to pack suitcases before the trip on {date}", "High"),
            ("Don't forget to take out the trash tonight", "Low"),
            ("Remind me to check the mail catalog today", "Low"),
            ("Set a reminder to write the daily journal entry at {time}", "Low")
        ],
        "Note": [
            ("Journal entry from today: {journal_texts}", "Low"),
            ("Bucket list ideas: visit {place} and learn to play the {instrument}", "Low"),
            ("Reflections on my day: {journal_texts}", "Low"),
            ("Hobby idea summary: {hobby_idea} looks very interesting", "Low"),
            ("Book recommendation list: read books on {topic}", "Low"),
            ("Recipe notes: ingredients for homemade pizza include cheese and tomatoes", "Low"),
            ("Movie wishlist: watch the new documentary about {topic}", "Low"),
            ("List of favorite songs to learn on the {instrument}", "Low"),
            ("Memorable moments from the trip to {place}", "Low"),
            ("Quotes that inspire me: progress is better than perfection", "Low")
        ]
    },
    "Finance": {
        "Task": [
            ("Pay the electricity and water bills before {date}", "High"),
            ("Transfer the monthly rent amount to {name}", "High"),
            ("File my quarterly tax returns before the deadline", "High"),
            ("Cancel the unused trial subscription to {service}", "Medium"),
            ("Update the monthly budget spreadsheet for {month}", "Medium"),
            ("Submit expense report for {project} reimbursement", "High"),
            ("Calculate travel expenses for the trip to {place}", "Medium"),
            ("Sell the shares of {stocks} stock", "High"),
            ("Transfer $100 to my savings account", "Medium"),
            ("Call the bank to dispute the unauthorized charge", "High")
        ],
        "Todo": [
            ("Review monthly credit card and bank statements", "Medium"),
            ("Compare auto insurance rates online", "Low"),
            ("Check the current price of {stocks} stock", "Low"),
            ("Research high-yield savings accounts", "Low"),
            ("Analyze investment portfolio allocation", "Medium"),
            ("Calculate total savings progress for this year", "Medium"),
            ("Audit digital subscriptions and memberships", "Medium"),
            ("Read financial planning blog post about stocks", "Low"),
            ("List down monthly fixed and variable expenses", "Medium"),
            ("Draft a budget plan for the upcoming trip", "Medium")
        ],
        "Reminder": [
            ("Remind me to pay the credit card bill on {date}", "High"),
            ("Remember to review investment options next Monday", "Medium"),
            ("Set a reminder for the auto-debit of {service} on {date}", "Medium"),
            ("Don't forget to send the rent payment by the 1st of the month", "High"),
            ("Remind me to check stock prices for {stocks} at {time}", "Low"),
            ("Remember to submit the tax documents by {date}", "High"),
            ("Set a reminder to pay the home insurance bill next week", "High"),
            ("Don't forget to withdraw cash from the ATM tomorrow", "Low"),
            ("Remind me to cancel the {service} subscription before {date}", "High"),
            ("Set a reminder to review budget limits on Saturday", "Medium")
        ],
        "Note": [
            ("Subscription cost tracker: {service} costs {money} per month", "Low"),
            ("Stock market watch: buy shares of {stocks} if price drops", "Low"),
            ("Savings plan: save {money} by the end of {month}", "Medium"),
            ("Bank account numbers and routing details saved here", "Medium"),
            ("Credit score update: reached 780 this month", "Medium"),
            ("Tax filing notes: keep receipts for business travel", "Medium"),
            ("Cryptocurrency wallet backup keys and seed words", "High"),
            ("Financial goals for {month}: limit dining out expenses to $150", "Medium"),
            ("Notes on investment strategy: focus on low-cost index funds", "Low"),
            ("Expense breakdown: spent {money} on groceries and {money} on utilities", "Medium")
        ]
    }
}

def fill_template(template, category, intent):
    """Fills a template string with random entities appropriate for the category."""
    # Mapping placeholders to lists of strings
    placeholders = {
        "{subject}": SUBJECTS,
        "{topic}": TOPICS,
        "{grocery}": GROCERIES,
        "{gadget}": GADGETS,
        "{item}": ITEMS,
        "{name}": NAMES,
        "{dept}": DEPTS,
        "{client}": CLIENTS,
        "{system}": SYSTEMS,
        "{project}": PROJECTS,
        "{medicine}": MEDICINES,
        "{place}": PLACES,
        "{instrument}": INSTRUMENTS,
        "{hobby_idea}": HOBBY_IDEAS,
        "{service}": SERVICES,
        "{month}": MONTHS,
        "{money}": MONEY,
        "{stocks}": STOCKS,
        "{time}": TIMES,
        "{date}": DATES,
        "{bp}": BPS,
        "{weight}": WEIGHTS,
        "{concept_detail}": CONCEPTS,
        "{note_detail}": NOTES,
        "{journal_texts}": JOURNAL_TEXTS,
        "{url}": [f"http://wikipedia.org/wiki/{random.choice(SUBJECTS)}", "https://github.com/trending", "https://youtube.com/learn", "http://arxiv.org/abs/1234"],
        "{num}": ["1", "2", "3", "4", "5", "10", "12", "20", "50"]
    }
    
    filled = template
    # Safe replacement loop (ensures multiple placeholders are handled)
    for placeholder, values in placeholders.items():
        while placeholder in filled:
            filled = filled.replace(placeholder, random.choice(values), 1)
            
    return filled

def main():
    print("Generating synthetic dataset...")
    
    dataset = []
    unique_texts = set()
    
    # We want at least 5000 examples. Let's aim for 5500 to be safe.
    target_count = 5500
    
    # Loop until target is met
    iterations = 0
    while len(dataset) < target_count and iterations < 100000:
        iterations += 1
        # Randomly choose a category, intent
        category = random.choice(list(TEMPLATES.keys()))
        intent = random.choice(list(TEMPLATES[category].keys()))
        
        # Pick a random template list
        template_list = TEMPLATES[category][intent]
        template_tuple = random.choice(template_list)
        
        template_text, base_priority = template_tuple
        
        # Fill it
        filled_text = fill_template(template_text, category, intent)
        
        # Avoid exact duplicates
        if filled_text.lower() in unique_texts:
            continue
            
        unique_texts.add(filled_text.lower())
        
        # Sometimes inject a date to make date extraction richer
        # Check if the text contains a date placeholder implicitly or if we want to append one
        text_to_save = filled_text
        if random.random() < 0.15 and not any(d in filled_text for d in ["tomorrow", "Monday", "Friday", "June", "July", "weekend", "tonight", "next week"]):
            time_suffix = random.choice([" tomorrow morning", " this Friday at 3pm", " next Monday at noon", " by next week", " tonight at 8 PM"])
            text_to_save += time_suffix
            
        # Sometimes inject priority words to enrich priority mapping
        priority = base_priority
        if random.random() < 0.10:
            if priority == "Low" and random.random() < 0.5:
                text_to_save = "ASAP: " + text_to_save
                priority = "High"
            elif priority == "High" and random.random() < 0.3:
                text_to_save += " (low priority though)"
                priority = "Low"
                
        dataset.append({
            "text": text_to_save,
            "intent": intent,
            "category": category,
            "priority": priority
        })

    # Save to CSV
    output_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "synthetic_dataset.csv")
    
    with open(output_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "intent", "category", "priority"])
        writer.writeheader()
        writer.writerows(dataset)
        
    print(f"Generated {len(dataset)} unique labeled examples saved to: {output_path}")

if __name__ == "__main__":
    main()
