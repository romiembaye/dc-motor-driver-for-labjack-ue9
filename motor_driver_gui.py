"""
Description : This is the source code for the project that interfaces with the LabJack UE9
              to provide drive capabilities for a DC Motor. The circuit will be connected to the LabJack
              UE9 using a DB-37 cable. The physical and logical pin connections are as follows:

              DB37 PIN  |   Logical PIN |   Used For
              --------------------------------------
              Pin 6     |   FIO -> 0    |   Enable/Disable and PWM
              Pin 24    |   FIO -> 1    |   Motor Terminal 1 (Forward)
              Pin 5     |   FIO -> 2    |   Motor Terminal 2 (Backward)
              Pin 23    |   FIO -> 3    |   Emergency Brake Input
              Pin 4     |   FIO -> 4    |   Reset Input
              Pin 1     |   GND         |   Ground Terminal

Binary Pin Layout:
        0b4(23)5(24)6

Connector Pin Layout: [ */** -> Physical Pin Connection ]
                                                           (*)  (*)  (*)         (*)
       |0| |0| |0| |0| |0| |0| |0| |0| |0| |0| |0| |0| |0| |6|  |5|  |4| |0| |0| |1|
         |0| |0| |0| |0| |0| |0| |0| |0| |0| |0| |0| |0| |0| |24| |23| |0| |0| |0|
                                                             (**) (**)
Operating Frequency:
        732.42 Hz -> 48MHz / 1 / 65536
"""

from tkinter import *                                                       # Library for the GUI
import os                                                                   # Library for checking correct UE9 IP
#import ue9                                                                 # Library to send/receive data
#import LabJackPython                                                       # Library for LabJack communication


class MotorDriver:
    resetPressed = False                                                    # Variable used to check Reset press
    eBrakePressed = False                                                   # Variable used to check Brake press
    motorRunning = False                                                    # Variable used to check operation
    previousTimerValue = int(60 * 655.35)                                   # Variable used to track PWM value
    previousDirection = 2                                                   # Variable used to track direction
    labJackFIOMask = 0b11111                                                # Variable sets FIO channel updates
    labJackFIODir = 0b00111                                                 # Variable sets FIO channel direction
    labJackFIOState = 0b11111                                               # Variable sets FIO channel state
    # labJackDriver             Created in the setLabJackIP method          # Variable for the LabJack connection
    # ip                        Created in the __init__ method              # Variable used to get the IP Address
    # password                  Created in the reset method                 # Variable used to get the password

    def __init__(self):
        """DOCUMENTATION GOES HERE"""
        """
        This function initializes the MotorDriver object with all the GUI elements
        and their current states (Disabled or Enabled)
        """
        self.window = Tk()                                                  # The main GUI window
        """
        This frame contains the tittle of the program
        """
        frmTittle = Frame()                                                 # Create a new frame (Tittle)
        frmTittle.pack(side=TOP)                                            # Place it in the main window
        picTittle = PhotoImage(file="etd555tittle.png")                     # Get an image for the ETD label
        lblTittle = Label(frmTittle, image=picTittle)                       # Create the label
        lblTittle.image = picTittle                                         # Hold a reference to the etd image
        lblTittle.pack(side=TOP)                                            # Place it in the Tittle frame
        """
        This frame contains the entry box for the LabJack IP Address
        """
        frmIpAddress = Frame()                                              # Create a new frame (IP Address)
        frmIpAddress.pack(side=TOP)                                         # Place it in the main window
        Label(frmIpAddress,
              text="LabJack's IP", bd=6, relief=FLAT).pack(side=LEFT)       # Place a label in the IP frame
        self.ip = Entry(frmIpAddress, bd=6, relief=RIDGE, justify=CENTER)   # Create a text entry box for the IP
        self.ip.bind("<Return>", self.setLabJackIP)                         # Bind the ENTER key to call a method
        self.ip.pack(side=LEFT)                                             # Place it in the IP Address frame
        picConnect = PhotoImage(file="connect.png")                         # Get an image for the connect button
        self.btnConnect = Button(frmIpAddress,
                                 relief=FLAT, image=picConnect,
                                 command=self.setLabJackIP)                 # Create the connect button
        self.btnConnect.image = picConnect                                  # Hold a reference to the image
        self.btnConnect.pack(side=LEFT)                                     # Place it in the IP Address frame
        """
        This frame contains the status of the program. It includes the 
        Turn ON and Turn OFF buttons that control the circuit operation
        of the motor
        """
        frmStatus = Frame(height=15)                                        # Create a new frame (Status)
        frmStatus.pack(side=TOP)                                            # Place it in the main window
        Label(frmStatus, text="STATUS").pack(side=LEFT)                     # Place a label in the Status frame
        picOff = PhotoImage(file="off.png")                                 # Get an image for the OFF button
        self.btnOFF = Button(frmStatus, relief=FLAT,
                             image=picOff, state=DISABLED,
                             command=lambda: self.statusOff(True))          # Create the button
        self.btnOFF.image = picOff                                          # Hold a reference to the off image
        self.btnOFF.pack(side=LEFT)                                         # Place it in the Status frame
        picOn = PhotoImage(file="on.png")                                   # Get an image for the ON button
        self.btnON = Button(frmStatus, relief=FLAT,
                            image=picOn, state=DISABLED,
                            command=self.statusOn)                          # Create the button
        self.btnON.image = picOn                                            # Hold a reference to the on image
        self.btnON.pack(side=LEFT)                                          # Place it in the Status frame
        """
        This frame contains the direction of the program. It includes the
        Go Forwards and Go Backwards buttons that controls the direction
        of the motor
        """
        frmDirection = Frame()                                              # Create a new frame (Direction)
        frmDirection.pack(side=TOP)                                         # Place it in the main window
        Label(frmDirection, text="DIRECTION").pack(side=LEFT)               # Place a label in the Direction frm
        picBackwards = PhotoImage(file="backwards.png")                     # Get an image for the BACKWARDS btn
        self.btnBackward = Button(frmDirection, image=picBackwards,
                                  relief=FLAT, state=DISABLED,
                                  command=self.backwardsDirection)          # Create the button
        self.btnBackward.image = picBackwards                               # Hold a reference to the back image
        self.btnBackward.pack(side=LEFT)                                    # Place it in the Direction frame
        picForwards = PhotoImage(file="forwards.png")                       # Get an image for the FORWARDS btn
        self.btnForward = Button(frmDirection, image=picForwards,
                                 relief=FLAT, state=DISABLED,
                                 command=self.forwardDirection)             # Create the button
        self.btnForward.image = picForwards                                 # Hold a reference to the forward img
        self.btnForward.pack(side=LEFT)                                     # Place it in the Direction frame
        """
        This frame contains the speed of the program. It includes the
        slider that controls the speed of the motor
        """
        frmSpeed = Frame()                                                  # Create a new frame (Speed)
        frmSpeed.pack(side=TOP)                                             # Place it in the main window
        Label(frmSpeed, text="SPEED").pack(side=LEFT)                       # Place a label in the Speed frame
        picSlow = PhotoImage(file="slowTurtle.png")                         # Get an image for the SLOW label
        lblSlow = Label(frmSpeed, image=picSlow)                            # Create the label
        lblSlow.image = picSlow                                             # Hold a reference to the slow image
        lblSlow.pack(side=LEFT)                                             # Place it in the Speed frame
        self.speedSlider = Scale(frmSpeed, from_=30, to=100,
                                 orient='horizontal',
                                 length=int(self.window.winfo_screenwidth() / 4),
                                 command=self.speedControl)                 # Create a slider scale from 30 - 100
        self.speedSlider.set(60)                                            # Set the default slider value to 60
        self.speedSlider.config(state=DISABLED, showvalue=0)                # Disable it and hide its value
        self.speedSlider.pack(side=LEFT, fill=X)                            # Place it in the Speed frame
        picFast = PhotoImage(file="fastRabbit.png")                         # Get an image for the FAST label
        lblFast = Label(frmSpeed, image=picFast)                            # Create the label
        lblFast.image = picFast                                             # Hold a reference to the fast image
        lblFast.pack(side=LEFT)                                             # Place it in the Speed frame
        self.window.resizable(False, False)                                 # Make it un-resizable
        self.window.title("Motor Driver")                                   # Set it's tittle to Motor Driver
        self.window.geometry(
            '+' + str(int(self.window.winfo_screenwidth() / 2) -
                      int(self.window.winfo_screenwidth() / 3)) +
            '+' + str(int(self.window.winfo_screenheight() / 2) -
                      int(self.window.winfo_screenheight() / 3)))           # Set where the main window appears
        self.window.protocol("WM_DELETE_WINDOW", self.terminateProgram)     # Set what the 'X' window button does
        self.ip.focus()                                                     # Set the focus on the IP entry box
        self.window.mainloop()                                              # Run the main window in a loop

    def terminateProgram(self):
        """DOCUMENTATION GOES HERE"""
        """
        This function is used to handle the closing of the program
        by turning the motor driver circuit OFF before termination
        """
        self.statusOff()                                                    # Call the statusOff method
        self.window.destroy()                                               # Close the main GUI window

    def setLabJackIP(self, event=None):
        """DOCUMENTATION GOES HERE"""
        """
        This function is used to update the LabJack's IP Address
        from within the GUI
        :param event: This is an event that is passed if the 'ENTER'
                      key was pressed from within the IP entry box.
                      It's value is 'None' if the Connect button is used
        """
        ipAddress = self.ip.get()                                           # Get the value from the IP entry box
        if not os.system("ping -n 1 " + ipAddress):                         # If pinging the IP address succeeds
            try:
                self.labJackDriver = ue9.UE9(ipAddress=ipAddress,
                                             ethernet=True)                 # Try to establish LabJack connection
                self.ip.config(bg="green", fg="white")                      # Update the Entry box GUI (SUCCESS)
                print("Connected to LabJack at", ipAddress)                 # Console -> print Connected...
                self.reset()                                                # Call the reset method
                self.emergencyBrake()                                       # Call the emergencyBrake method
                self.statusOff()                                            # Call the statusOff method
            except:                                                         # If the IP is not of a LabJack UE9
                print("Failed to connect to LabJack at", ipAddress)         # Console -> print Failed...
                self.ip.config(bg="red", fg="white")                        # Update the Entry box GUI (ERROR)
                pass                                                        # Keep going
        else:                                                               # If ping failed
            print("Failed to connect to LabJack at", ipAddress)             # Console -> print Failed
            self.ip.config(bg="red", fg="white")                            # Update the Entry box GUI (ERROR)
    
    def statusOn(self):
        """DOCUMENTATION GOES HERE"""
        """
        This function is used to turn the motor driver circuit on
        """
        if self.eBrakePressed:                                              # If the E-Brake has been triggered
            self.reset(True)                                                # Call the reset method and pass TRUE
        else:                                                               # If the E-Brake was not triggered
            self.btnON.config(state=DISABLED)                               # Disable the ON button
            self.btnOFF.config(state=ACTIVE)                                # Enable the OFF button
            self.btnBackward.config(state=ACTIVE)                           # Enable the BACKWARDS button
            self.btnForward.config(state=ACTIVE)                            # Enable the FORWARDS button
            self.speedSlider.config(state=ACTIVE, showvalue=1)              # Enable the SPEED control slider
            self.motorRunning = True                                        # Set the circuit operation to TRUE
            self.labJackDriver.timerCounter(TimerClockBase=1,               # Set Base Clk to System Clk (48Mhz)
                                            TimerClockDivisor=1,            # Set Clock Divisor to 1
                                            Timer0Mode=0,                   # Set Timer Mode to 16-bit (65,536)
                                            NumTimersEnabled=1,             # Set the number of enabled timers
                                            UpdateConfig=1,                 # Set Update Timer parameter to True
                                            Timer0Value=self.previousTimerValue)    # Set the Timer Value
            self.labJackFIOState = 0b11110                                  # Turn the Enable pin to low->Turn ON
            self.labJackDriver.feedback(FIOMask=self.labJackFIOMask,        # Set the UE9 pin Masks (Update)
                                        FIODir=self.labJackFIODir,          # Set the UE9 pin Dirs (Direction)
                                        FIOState=self.labJackFIOState)      # Set the UE9 pin States (HI or LOW)

            print("Motor Driver is ON")                                     # Console -> print ON
    
    def statusOff(self, turnOFF=False):
        """DOCUMENTATION GOES HERE"""
        """
        This function is used to turn the motor driver circuit off
        :param turnOFF: This is a boolean value used to check if the Turn OFF
                        button was used to stop the Driver (Motor) instead of
                        the Emergency Button being triggered.
                        It's value is False if the E-Brake button is used
        """
        self.btnON.config(state=ACTIVE)                                     # Enable the ON button
        self.btnOFF.config(state=DISABLED)                                  # Disable the OFF button
        self.btnBackward.config(state=DISABLED)                             # Disable the BACKWARDS button
        self.btnForward.config(state=DISABLED)                              # Disable the FORWARDS button
        self.speedSlider.config(state=DISABLED, showvalue=0)                # Disable the SPEED control slider
        if self.motorRunning:                                               # If the Driver (Motor) is ON
            self.labJackDriver.timerCounter(TimerClockBase=1,               # Set Base Clk to System Clk (48Mhz)
                                            TimerClockDivisor=1,            # Set Clock Divisor to 1
                                            Timer0Mode=0,                   # Set Timer Mode to 16-bit (65,536)
                                            NumTimersEnabled=0,             # Set the number of enabled timers
                                            UpdateConfig=1,                 # Set Update Timer parameter to True
                                            Timer0Value=0)                  # Set the Timer Value
            self.labJackFIOState = 0b11111                                  # Turn the Enable pin to hi->Turn OFF
            self.labJackDriver.feedback(FIOMask=self.labJackFIOMask,        # Set the UE9 pin Masks (Update)
                                        FIODir=self.labJackFIODir,          # Set the UE9 pin Dir (Direction)
                                        FIOState=self.labJackFIOState)      # Set the UE9 pin States (HI or LOW)
            self.motorRunning = False                                       # Set the circuit operation to FALSE
        if turnOFF:                                                         # If the Turn Off button is used
            self.previousDirection = 2                                      # Set the direction variable to NONE

        print("Motor Driver is OFF")                                        # Console -> print OFF
    
    def forwardDirection(self):
        """DOCUMENTATION GOES HERE"""
        """
        This function is used to rotate the motor in the *forwards direction
        """
        self.btnForward.config(state=DISABLED)                              # Disable the FORWARDS button
        self.btnBackward.config(state=ACTIVE)                               # Enable the BACKWARDS button

        self.labJackFIOState = 0b11111                                      # Turn the En, Frd, Brd pins to hi
        self.labJackDriver.feedback(FIOMask=self.labJackFIOMask,
                                    FIODir=self.labJackFIODir,
                                    FIOState=self.labJackFIOState)          # Turn Off the Driver
        self.window.after(100)                                              # Wait 100 milli seconds
        self.labJackFIOState = 0b11100                                      # Turn the En, Frd pins to low
        self.labJackDriver.feedback(FIOMask=self.labJackFIOMask,
                                    FIODir=self.labJackFIODir,
                                    FIOState=self.labJackFIOState)          # Turn On the Driver and go Forwards
        self.previousDirection = 0                                          # Set the direction variable to frd
        
        print("Motor Driver in FORWARD Direction")                          # Console -> print FORWARDS
    
    def backwardsDirection(self):
        """DOCUMENTATION GOES HERE"""
        """
        This function is used to rotate the motor in the *backwards direction
        """
        self.btnForward.config(state=ACTIVE)                                # Enable the FORWARDS button
        self.btnBackward.config(state=DISABLED)                             # Disable the BACKWARDS button

        self.labJackFIOState = 0b11111                                      # Turn the En, Frd, Brd pins to hi
        self.labJackDriver.feedback(FIOMask=self.labJackFIOMask,
                                    FIODir=self.labJackFIODir,
                                    FIOState=self.labJackFIOState)          # Turn Off the Driver
        self.window.after(100)                                              # Wait 100 milli seconds
        self.labJackFIOState = 0b11010                                      # Turn the En, Brd pins to low
        self.labJackDriver.feedback(FIOMask=self.labJackFIOMask,
                                    FIODir=self.labJackFIODir,
                                    FIOState=self.labJackFIOState)          # Turn On the Driver and go Backwards
        self.previousDirection = 1                                          # Set the direction variable to Brd
        
        print("Motor Driver in BACKWARDS Direction")                        # Console -> print BACKWARDS
    
    def speedControl(self, dutyCycle):
        """DOCUMENTATION GOES HERE"""
        """
        This function is used to control the speed of the motor
        :param dutyCycle: This is an integer value from 30 to 100
                          obtained from the slider
        The PWM frequency is (732.421875 Hz)
        """
        if self.motorRunning:
            dCTimerValue = int(dutyCycle) * 655.35                          # Convert the D.C. -> Timer Value
            self.labJackDriver.timerCounter(TimerClockBase=1,               # Set Base Clk to System Clk (48Mhz)
                                            TimerClockDivisor=1,            # Set Clock Divisor to 1
                                            Timer0Mode=0,                   # Set Timer Mode to 16-bit (65,536)
                                            NumTimersEnabled=1,             # Set the number of enabled timers
                                            UpdateConfig=1,                 # Set Update Timer parameter to True
                                            Timer0Value=int(dCTimerValue))  # Set the Timer Value
            self.previousTimerValue = int(dCTimerValue)                     # Update the timer value variable

            print("Duty Cycle at", dutyCycle, "% =", self.previousTimerValue)   # Console -> print D.C.,TimerVal
    
    def emergencyBrake(self):
        """DOCUMENTATION GOES HERE"""
        """
        This function is used to check if the emergency stop has been
        triggered and if so, immediately stop the motor
        """
        ebrakecheck = self.labJackDriver.feedback(FIOMask=self.labJackFIOMask,
                                                  FIODir=self.labJackFIODir,
                                                  FIOState=self.labJackFIOState)    # Get value from eBrake pin
        if not ebrakecheck["FIOState"] & 0b01000 and self.motorRunning:     # If Circuit ON and E-Brake pressed
            print("EMERGENCY BRAKE Triggered")                              # Console -> print EMERGENCY BRAKE

            self.eBrakePressed = True                                       # Set Brake triggered variable True
            self.statusOff()                                                # Call the statusOff function
            self.eBrake = Toplevel()                                        # Set up a secondary window (eBrake)
            self.eBrake.overrideredirect(True)                              # Remove the window (Min, Max, Exit)
            self.eBrake.resizable(False, False)                             # Make the window un-resizable
            self.eBrake.title("Brake")                                      # Set it's tittle to BRAKE
            self.eBrake.grab_set()                                          # Take control away from main window
            self.eBrake.geometry(
                '+' + str(int(self.eBrake.winfo_screenwidth() / 2) -
                          int(self.eBrake.winfo_screenwidth() / 4.5)) +
                '+' + str(int(self.eBrake.winfo_screenheight() / 2) -
                          int(self.eBrake.winfo_screenheight() / 24)))      # Set where the eBrake window appears
            Label(self.eBrake,
                  text="Emergency Brake Activated",
                  font=("Courier", 24), fg="red",
                  bg="black").pack(fill=BOTH)                               # Place a label in the eBrake window
            brakeIcon = PhotoImage(file="brake.png")                        # Get an image for the eBrake button
            btnBrake = Button(self.eBrake, image=brakeIcon,
                              bg="black", bd=20,
                              command=self.eBrake.destroy)                  # Create the button
            btnBrake.image = brakeIcon                                      # Hold a reference to the brake image
            btnBrake.pack(fill=BOTH)                                        # Place it in the eBrake window
            self.eBrake.update()                                            # Update the eBrake window
            btnBrake.flash()                                                # Flash the eBrake acknowledge button
        self.window.after(10, self.emergencyBrake)                          # Reset to check every 10 milli sec
    
    def reset(self, turnON=False):
        """DOCUMENTATION GOES HERE"""
        """
        This function is used to check if the reset has been triggered
        and if so, check if the user has confirmed it in the GUI and then
        reset (start) the motor
        :param turnON: This is a boolean value used to check if the Turn ON
                       button was used to start the Driver (Motor) after the
                       Emergency Button was triggered.
                       It's value is False if the Reset button is used
        """
        def resetContinue(event=None):
            """DOCUMENTATION GOES HERE"""
            """
            This function is used to close the eReset window and start the motor
            :param event: This is an event that is passed if the 'ENTER'
                          key was pressed from within the PASSWORD entry box.
                          It's value is 'None' if the Reset button is used
            """
            if self.password.get() == "go":                                 # If the password entered matches
                self.eBrakePressed = False                                  # Set Brake triggered variable False
                self.eBrake.destroy()                                       # Close the E-Brake window if active
                self.statusOn()                                             # Call the statusOn function
                if self.previousDirection == 1:                             # If the Direction Variable is 1
                    self.backwardsDirection()                               # Go Backwards
                elif self.previousDirection == 0:                           # If the Direction Variable is 0
                    self.forwardDirection()                                 # Go Forwards
                self.resetPressed = False                                   # Set Reset triggered variable False
                eReset.destroy()                                            # Close the eReset prompt window
            else:                                                           # If the password doesn't match
                self.password.config(bg="red", fg="white")                  # Update the Entry box GUI (ERROR)
                eReset.update()                                             # Update the eReset window
                self.btnReset.flash()                                       # Flash the Reset confirmation button
                eReset.after(1000)                                          # Wait a 1 second
                self.password.config(bg="white", fg="black")                # Update the Entry box GUI (NORMAL)
                
        resetCheck = self.labJackDriver.feedback(FIOMask=self.labJackFIOMask,
                                                 FIODir=self.labJackFIODir,
                                                 FIOState=self.labJackFIOState)     # Get value from Reset pin
        
        if (not resetCheck["FIOState"] & 0b10000 and                        # If Reset was pressed **AND**
                not self.motorRunning and                                   # Driver (Motor) is Off **AND**
                not self.resetPressed and                                   # Reset variable is False **AND**
                self.eBrakePressed) or turnON:                              # E-brake variable is True ***** OR
                                                                            # turnON is True->Turn ON button used
            print("RESET Triggered")                                        # Console -> print RESET

            self.resetPressed = True                                        # Set Reset triggered variable True
            eReset = Toplevel()                                             # Set up a secondary window (eReset)
            eReset.resizable(False, False)                                  # Make the window un-resizable
            eReset.overrideredirect(True)                                   # Remove the window (Min, Max, Exit)
            eReset.title("Reset")                                           # Set it's tittle to RESET
            eReset.grab_set()                                               # Take control away from main window
            eReset.geometry(
                '+' + str(int(eReset.winfo_screenwidth() / 2) -
                          int(eReset.winfo_screenwidth() / 4.3)) +
                '+' + str(int(eReset.winfo_screenheight() / 2) -
                          int(eReset.winfo_screenheight() / 24)))           # Set where the eReset window appears
            Label(eReset, text="Reset. Enter your password to continue...",
                  font=("Courier", 15), fg="white",
                  bg="black").pack(fill=BOTH)                               # Place a label in the eReset window
            self.password = Entry(eReset, bd=6, relief=RIDGE,
                                  justify=CENTER, show="*")                 # Create a password Entry box
            self.password.bind("<Return>", resetContinue)                   # Bind the ENTER key to call a method
            self.password.pack(fill=BOTH)                                   # Place it in the eReset window
            resetIcon = PhotoImage(file="reset.png")                        # Get an image for the eReset button
            self.btnReset = Button(eReset, image=resetIcon,
                                   bg="black", bd=10,
                                   command=resetContinue)                   # Create the button
            self.btnReset.image = resetIcon                                 # Hold a reference to the reset image
            self.btnReset.pack(fill=BOTH)                                   # Place it in the eReset window
            self.password.focus()                                           # Set the focus on the password field
            eReset.update()                                                 # Update the eReset window
            self.btnReset.flash()                                           # Flash the Reset button
        self.window.after(10, self.reset)                                   # Reset to check every 10 milli sec
# End of Class


dCMotorDriver = MotorDriver()                                               # Create an instance(Run the Program)
