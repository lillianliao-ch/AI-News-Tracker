from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)
CORS(app) # Enable CORS for extension communication

# Generate a timestamped filename when the server starts
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
# Save to Downloads folder
downloads_path = os.path.expanduser('~/Downloads')
DATA_FILE = os.path.join(downloads_path, f'candidates_{timestamp}.csv')
print(f"Server started. Data will be saved to: {os.path.abspath(DATA_FILE)}")

def save_to_csv(data):
    """Save data to CSV with specific column order"""
    # Define the exact column order
    columns = [
        'name', 'birth_date', 'age', 'city', 'work_years', 'education',
        'phone', 'email', 'current_company', 'current_position', 'active_status',
        'work_experience', 'education_history', 'url', 'scraped_at'
    ]
    
    df = pd.DataFrame([data], columns=columns)
    
    if not os.path.isfile(DATA_FILE):
        df.to_csv(DATA_FILE, index=False)
    else:
        df.to_csv(DATA_FILE, mode='a', header=False, index=False)

def calculate_age(birth_year):
    """Calculate age from birth year"""
    if not birth_year:
        return ''
    try:
        birth_year = int(str(birth_year)[:4])  # Extract year
        current_year = datetime.now().year
        return current_year - birth_year
    except:
        return ''

def calculate_work_years(work_experience_list):
    """Calculate total work years from work experience"""
    if not work_experience_list or not isinstance(work_experience_list, list):
        return ''
    
    import re
    total_months = 0
    
    for exp in work_experience_list:
        # Look for patterns like "7年4个月" or "3个月" or "1年11个月"
        years_match = re.search(r'(\d+)年', exp)
        months_match = re.search(r'(\d+)个月', exp)
        
        if years_match:
            total_months += int(years_match.group(1)) * 12
        if months_match:
            total_months += int(months_match.group(1))
    
    if total_months == 0:
        return ''
    
    years = total_months // 12
    months = total_months % 12
    if months > 0:
        return f"{years}年{months}个月"
    else:
        return f"{years}年"

def extract_latest_education(education_list):
    """Extract the latest (first) education entry"""
    if not education_list or not isinstance(education_list, list) or len(education_list) == 0:
        return ''
    
    # The first entry is usually the most recent
    latest = education_list[0]
    # Extract just the school and degree info, skip the date range
    lines = latest.split('\n')
    if len(lines) >= 2:
        # Usually format is: date range, school name, degree
        return ' '.join(lines[1:]).strip()
    return latest.strip()

def parse_active_status(active_status_text):
    """Extract time portion from active status like '最近联系 2天前'"""
    if not active_status_text:
        return ''
    
    import re
    # Look for patterns like "2天前", "3小时前", "刚刚" after "最近联系"
    if '最近联系' in active_status_text:
        # Extract everything after "最近联系"
        parts = active_status_text.split('最近联系')
        if len(parts) > 1:
            time_part = parts[1].strip()
            # Extract just the time expression (e.g., "2天前")
            match = re.search(r'(\d+[天小时分钟]+前|刚刚)', time_part)
            if match:
                return match.group(1)
            return time_part
    
    # If no "最近联系", try to find time patterns directly
    match = re.search(r'(\d+[天小时分钟]+前|刚刚)', active_status_text)
    if match:
        return match.group(1)
    
    return active_status_text

def extract_current_company_position(work_experience_list, basic_info):
    """Extract current company and position from work experience or basic_info"""
    current_company = basic_info.get('当前公司', '')
    current_position = basic_info.get('当前职位', '')
    
    # If not in basic_info, try to extract from first work experience
    if (not current_company or not current_position) and work_experience_list and isinstance(work_experience_list, list) and len(work_experience_list) > 0:
        first_exp = work_experience_list[0]
        lines = first_exp.split('\n')
        
        # Try to find company name (usually on second line)
        if len(lines) > 1:
            if not current_company:
                current_company = lines[1].strip()
        
        # Try to find position (usually after location info)
        for i, line in enumerate(lines):
            if not current_position and i > 2:  # Position usually appears after date and company
                # Skip lines that look like dates, durations, or locations
                if not any(keyword in line for keyword in ['年', '个月', '至今', '-', '所有']):
                    current_position = line.strip()
                    break
    
    return current_company, current_position

def analyze_experience(work_exp_text):
    """
    Placeholder for analysis logic.
    Returns True if candidate is suitable, False otherwise.
    """
    if not work_exp_text:
        return False
    
    # Simple example filter: Check for keywords
    keywords = ['Java', 'Python', 'Engineer', 'Manager']
    # If any keyword is present, keep it.
    # This is very basic, can be expanded.
    for kw in keywords:
        if kw.lower() in work_exp_text.lower():
            return True
            
    return True # Default to True for now to capture everything

@app.route('/api/save_candidate', methods=['POST'])
def save_candidate():
    data = request.json
    print(f"DEBUG: Received candidate data payload: {data}")
    print(f"DEBUG: Candidate Name: {data.get('name')}")
    
    # Analyze
    work_exp = data.get('work_experience', [])
    if isinstance(work_exp, list):
        work_exp_str = " ".join(work_exp)
    else:
        work_exp_str = str(work_exp)
        
    is_suitable = analyze_experience(work_exp_str + " " + str(data.get('basic_info', '')))
    
    if is_suitable:
        # Parse basic_info
        basic_info = data.get('basic_info', {})
        
        # Extract and calculate fields
        birth_date = basic_info.get('生日', '') if isinstance(basic_info, dict) else ''
        age = calculate_age(birth_date)
        work_years = calculate_work_years(work_exp if isinstance(work_exp, list) else [])
        education_latest = extract_latest_education(data.get('education', []))
        active_status_parsed = parse_active_status(data.get('active_status', ''))
        current_company, current_position = extract_current_company_position(
            work_exp if isinstance(work_exp, list) else [], 
            basic_info if isinstance(basic_info, dict) else {}
        )
        
        # Build the final data structure with correct column order
        final_data = {
            'name': data.get('name', ''),
            'birth_date': birth_date,
            'age': age,
            'city': basic_info.get('所在城市', '') if isinstance(basic_info, dict) else '',
            'work_years': work_years,
            'education': education_latest,
            'phone': basic_info.get('手机', '').replace('手机: ', '') if isinstance(basic_info, dict) else '',
            'email': basic_info.get('邮箱', '').replace('私人: ', '').replace('工作: ', '') if isinstance(basic_info, dict) else '',
            'current_company': current_company,
            'current_position': current_position,
            'active_status': active_status_parsed,
            'work_experience': ' | '.join(work_exp) if isinstance(work_exp, list) else str(work_exp),
            'education_history': ' | '.join(data.get('education', [])) if isinstance(data.get('education', []), list) else str(data.get('education', '')),
            'url': data.get('url', ''),
            'scraped_at': datetime.now().isoformat()
        }
        
        save_to_csv(final_data)
        return jsonify({"status": "saved", "message": "Candidate saved"}), 200
    else:
        print("Candidate filtered out.")
        return jsonify({"status": "filtered", "message": "Candidate did not meet criteria"}), 200

@app.route('/api/log', methods=['POST'])
def log_message():
    data = request.json
    print(f"[EXTENSION LOG]: {data.get('message')}")
    return jsonify({"status": "ok"}), 200

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Server is running"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5001)
