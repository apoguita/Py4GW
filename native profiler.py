import PyImGui
from Py4GWCoreLib import ThrottledTimer
import Py4GW

initialized = False
update_timer = ThrottledTimer(1000)  # Update every 1000 ms
metric_names = []
metrics_dict = {}

def main():
    global initialized
    global metric_names
    global metrics_dict
    global update_timer
    
    if update_timer.IsExpired():
        initialized = False  # Force reinitialization to refresh data
        update_timer.Reset()
    
    if not initialized:
        initialized = True
        
        metric_names = Py4GW.Console.get_profiler_metric_names()
        reports = Py4GW.Console.get_profiler_reports()
        metrics_dict = {
            name: {
                "min": min_time,
                "avg": avg_time,
                "p50": p_50,
                "p95": p_95,
                "p99": p_99,
                "max": max_tim
        }
            for name, min_time, avg_time, p_50, p_95, p_99, max_tim in reports
        }
        
    if PyImGui.begin("Profiler Data"):
        
        for name in metric_names:
            if name in metrics_dict:
                data = metrics_dict[name]
                PyImGui.text(f"{name}: Min={data['min']:.2f}ms, Avg={data['avg']:.2f}ms, P50={data['p50']:.2f}ms, P95={data['p95']:.2f}ms, P99={data['p99']:.2f}ms, Max={data['max']:.2f}ms")
            else:
                PyImGui.text(f"{name}: No data available")
        


    PyImGui.end()

if __name__ == "__main__":
    main()