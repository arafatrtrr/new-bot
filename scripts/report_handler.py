import os
import csv
import threading
from datetime import datetime, timezone, timedelta

DHAKA_TZ = timezone(timedelta(hours=6))

class BatchStats:
    def __init__(self, total_instances):
        self.lock = threading.Lock()
        self.total = total_instances
        self.view_count = 0
        self.completed_count = 0
        self.errors_count = 0
        self.error_details = [] 

    def register_view_reached(self):
        with self.lock:
            self.view_count += 1

    def register_click_success(self):
        with self.lock:
            self.view_count -= 1 

    def register_completion(self):
        with self.lock:
            self.completed_count += 1

    def register_error(self, instance_id, reason, page, domain, was_view=False):
        with self.lock:
            detail = f"[Inst-{instance_id}] {reason} | Page: {page} | Dom: {domain}"
            self.error_details.append(detail)
            if not was_view:
                self.errors_count += 1

class ReportSession:
    def __init__(self):
        self.base_dir = "report"
        now_str = datetime.now(DHAKA_TZ).strftime("%Y-%m-%d_%H-%M-%S")
        self.session_folder = os.path.join(self.base_dir, f"report_{now_str}")
        if not os.path.exists(self.session_folder): os.makedirs(self.session_folder)
            
        self.csv_file = os.path.join(self.session_folder, "report.csv")
        self.html_file = os.path.join(self.session_folder, "report.html")
        self._init_csv()
        
        self.total_batches = 0
        self.session_views = 0
        self.session_completed = 0
        self.session_errors = 0
        self.start_time = datetime.now(DHAKA_TZ)
        self.batch_history = []

    def _init_csv(self):
        headers = ["Batch", "View", "Completed", "Errors", "Duration", "Start", "End", "Error Details"]
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(headers)

    def log_batch(self, batch_num, stats, start_dt, end_dt):
        duration = str(end_dt - start_dt).split('.')[0]
        # Use 12-hour format with %p
        start_str = start_dt.strftime("%I:%M:%S %p")
        end_str = end_dt.strftime("%I:%M:%S %p")
        
        error_str = " ; ".join(stats.error_details) if stats.error_details else "None"

        self.total_batches += 1
        self.session_views += stats.view_count
        self.session_completed += stats.completed_count
        self.session_errors += stats.errors_count

        row = [batch_num, stats.view_count, stats.completed_count, stats.errors_count, duration, start_str, end_str, error_str]
        
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(row)
            
        self.batch_history.append(row)
        self._generate_html()
        return row

    def _generate_html(self):
        end_time = datetime.now(DHAKA_TZ)
        session_duration = str(end_time - self.start_time).split('.')[0]
        
        html = f"""
        <html>
        <head>
            <title>Automation Report</title>
            <style>
                body {{ font-family: sans-serif; padding: 20px; background: #f4f4f4; }}
                table {{ width: 100%; border-collapse: collapse; background: #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                th, td {{ padding: 10px; border-bottom: 1px solid #ddd; text-align: left; vertical-align: top; }}
                th {{ background: #007bff; color: white; }}
                .summary {{ background: white; padding: 15px; margin-bottom: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .err-detail {{ font-size: 0.85em; color: #d9534f; }}
                .meta {{ color: #666; font-size: 0.9em; margin-bottom: 10px; }}
            </style>
        </head>
        <body>
            <h1>Session Report</h1>
            <div class="summary">
                <div class="meta">
                    <strong>Start:</strong> {self.start_time.strftime("%Y-%m-%d %I:%M:%S %p")} | 
                    <strong>End:</strong> {end_time.strftime("%Y-%m-%d %I:%M:%S %p")} | 
                    <strong>Duration:</strong> {session_duration}
                </div>
                <hr>
                <p><strong>Total Batches:</strong> {self.total_batches}</p>
                <p><strong>Total Completed:</strong> <span style="color:green">{self.session_completed}</span></p>
                <p><strong>Total Views (Partial):</strong> <span style="color:blue">{self.session_views}</span></p>
                <p><strong>Total Errors:</strong> <span style="color:red">{self.session_errors}</span></p>
            </div>
            <table>
                <tr>
                    <th>Batch</th><th>View</th><th>Comp</th><th>Err</th><th>Dur</th><th>Start</th><th>End</th><th>Details</th>
                </tr>
        """
        for r in self.batch_history:
            err_html = r[7].replace(" ; ", "<br>")
            html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td><td>{r[6]}</td><td class='err-detail'>{err_html}</td></tr>"
            
        html += "</table></body></html>"
        with open(self.html_file, 'w', encoding='utf-8') as f: f.write(html)

    def print_session_summary(self):
        end_time = datetime.now(DHAKA_TZ)
        duration = end_time - self.start_time
        duration_str = str(duration).split('.')[0]
        
        print("\n" + "="*50)
        print(f"       SESSION SUMMARY REPORT")
        print("="*50)
        print(f" Total Batches   : {self.total_batches}")
        print(f" Total Views     : {self.session_views}")
        print(f" Total Completed : {self.session_completed}")
        print(f" Total Errors    : {self.session_errors}")
        print("-" * 50)
        print(f" Session Duration: {duration_str}")
        print(f" Start Time      : {self.start_time.strftime('%I:%M:%S %p')}")
        print(f" End Time        : {end_time.strftime('%I:%M:%S %p')}")
        print("="*50 + "\n")
        print(f"Report saved to: {self.session_folder}")