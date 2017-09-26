import os
from pathlib import Path

DEFAULTS = dict(
    datadir='.',
    statefile=str(Path(os.environ['HOME']) / '.kcam_arm_state'),
    det_led_pin='24',
    act_led_pin='25',
    pwr_led_pin='27',
    arm_led_pin='17',
    arm_btn_pin='22',
    door_pin='4',
    motion_pin='23',
    temperature_pin='12',
    keypad_grab='true',
    buzzer_pwm_path='/sys/class/pwm/pwmchip0/pwm1',
    buzzer_enable='true',
)
