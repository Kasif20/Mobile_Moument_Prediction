#[link(name="android")]
unsafe extern "C" {}

use std::ffi::CStr;
use std::ptr;
use std::slice;

use pyo3::Bound;
use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;
use pyo3::PyErr;

use android_looper_sys::{
    ALooper, ALooper_pollOnce, ALooper_prepare, ALooper_release,
    LooperPrepareOpts,
};

use android_sensor_sys::{
    ASensor, ASensorEvent, ASensorEventQueue, ASensorManager,
    ASensorEventQueue_disableSensor, ASensorEventQueue_enableSensor,
    ASensorEventQueue_getEvents, ASensorEventQueue_setEventRate,
    ASensorManager_createEventQueue, ASensorManager_destroyEventQueue,
    ASensorManager_getDefaultSensor, ASensorManager_getInstance,
    ASensor_getName, //ASensor_getVendor,
};

use libc::c_int;

const ASENSOR_TYPE_ACCELEROMETER:c_int = 1;
const ASENSOR_TYPE_MAGNETIC_FIELD:c_int = 2;

const ALOOPER_PREPARE_ALLOW_NON_CALLBACKS:c_int = LooperPrepareOpts::AllowNonCallbacks as c_int;

#[repr(C)]
struct ASensorEventShadow{
    version: i32,
    sensor:  i32,
    event_type: i32,
    reserved0: i32,
    timestamp: i64,
    data:[f32;16],
}

#[pyclass(unsendable)]
pub struct SensorManager{
    manager: *mut ASensorManager,
    looper:  *mut ALooper,
    queue:   *mut ASensorEventQueue,
    sensor:  *const ASensor,
    sensor_type:c_int,
    enabled:bool,
}

fn Err_p<T>(error:&str)->Result<T,PyErr>{
    return Err(PyRuntimeError::new_err(error.to_string()));
}

#[pymethods]
impl SensorManager{
    #[new]
    pub fn new(sensor_type:c_int)->Result<SensorManager, PyErr>{
        unsafe{
            let manager = ASensorManager_getInstance();
            if manager.is_null(){
                return Err_p("Failed to get sensor manager");
            }
            let sensor = ASensorManager_getDefaultSensor(manager,sensor_type);
            if sensor.is_null(){
                return Err_p("Requested Sensor not found on this device");
            }
            let looper = ALooper_prepare(ALOOPER_PREPARE_ALLOW_NON_CALLBACKS);
            if looper.is_null(){
                return Err_p("Failed to prepare ALooper");
            }
            let queue = ASensorManager_createEventQueue(
                manager,
                looper,
                0,
                None,
                ptr::null_mut(),
                );
            if queue.is_null(){
                ALooper_release(looper);
                return Err_p("Failed to create sensor event queue");
            }
            if ASensorEventQueue_enableSensor(queue,sensor)<0{
                ASensorManager_destroyEventQueue(manager,queue);
                ALooper_release(looper);
                return Err_p("Failed to enable sensor"); 
            }

            let mut mgr = SensorManager{
                manager,
                looper,
                queue,
                sensor,
                sensor_type,
                enabled:true,
            };
            mgr.set_delay(200_000)?;
            Ok(mgr)
        }
    }


    pub fn set_delay(&mut self,microsecond:i32)->Result<(),PyErr>{
        unsafe{
            if self.queue.is_null() || self.sensor.is_null(){
                return Err_p("Sensor not initialized");
            }
            if ASensorEventQueue_setEventRate(self.queue, self.sensor, microsecond)<0{
                return Err_p("Failed to set Event Rate");
            }
            Ok(())
        }
    }

    pub fn poll_event(&mut self,timeout_ms:i32) -> Result<Vec<[f64;4]>,PyErr>{
        unsafe{
            if self.queue.is_null(){
                return Err_p("Sensor Queue not initilized");
            }

            let ident = ALooper_pollOnce(timeout_ms,ptr::null_mut(),ptr::null_mut(),ptr::null_mut());
            if ident < 0{
                println!("Timeout or Error");
                return Ok(Vec::new());
            }

            let mut event_buffer:[ASensorEvent;256]=std::mem::zeroed();
            let num_event = ASensorEventQueue_getEvents(
                self.queue,
                event_buffer.as_mut_ptr(),
                256,
                );
            if num_event < 0{
                return Err_p("Failed to get sensor Events");
            }
            let event = slice::from_raw_parts(event_buffer.as_ptr(),num_event as usize);
            let result = event.iter().map(|ev|{
                let ev_ptr = ev as *const ASensorEvent as *const  ASensorEventShadow;
                let ev_d = &*ev_ptr;
                [ev_d.timestamp as f64,
                ev_d.data[0] as f64,
                ev_d.data[1] as f64,
                ev_d.data[2] as f64,
                ]
            }).collect();
            Ok(result)
        }
    }

    pub fn get_sensor_name(&self) -> Option<String>{
        if self.sensor.is_null(){
            return None
        }
        unsafe{
            let name_ptr = ASensor_getName(self.sensor);
            if name_ptr.is_null(){
                return None;
            }
            else{
                Some(CStr::from_ptr(name_ptr).to_string_lossy().into_owned())
            }
        }
    }

    pub fn disable(&mut self){
        unsafe{
            if self.enabled && !self.sensor.is_null() && !self.queue.is_null(){
                ASensorEventQueue_disableSensor(self.queue,self.sensor);
                self.enabled = false;
            }
        }
    }
}

impl Drop for SensorManager{
    fn drop(&mut self){
        unsafe{
            if !self.manager.is_null() && !self.queue.is_null(){
                if self.enabled && !self.sensor.is_null(){
                    ASensorEventQueue_disableSensor(self.queue,self.sensor);
                }
                ASensorManager_destroyEventQueue(self.manager,self.queue);
            }
        }
    }
}

#[pymodule]
fn sensor_manager<'py>(m:&Bound<'py,PyModule>)->PyResult<()>{
    m.add_class::<SensorManager>()?;
    Ok(())
}
