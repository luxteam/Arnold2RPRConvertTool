
'''

Arnold to RadeonProRender Converter

History:
v.1.0 - first version
v.1.1 - aiStandartSurface support
v.1.2 - displacement, bump2d conversion
v.1.3 - aiSkyDomeLight and aiAreaLight support
v.1.4 - Opacity reverse node, rotate IBL and aiPhysicalSky support
v.1.5 - aiPhotometricLight support.
v.1.6 - Fix ies light position; aiStandartVolume, aiMixShader, aiFlat, aiSky, aiAdd, aiSubstract, aiDivide, aiMultiply support
v.1.7 - Fix bug with channel converting, fix bug with creating extra materials.
v.2.0 - Rewritten to python, update material conversion.
v.2.1 - aiMath nodes support
	aiImage and aiFacingRatio conversion support
	aiAmbientOcclusion material conversion support
	Improve metalness, coat, subsurface and normal map conversion in aiStandartSurface
	Improve displacement conversion
	Fixed issue with group of lights
	Fixed issue with unassign materials with shader catcher
v.2.2 - Fixed bug with unsupported nodes conversion


'''

import maya.mel as mel
import maya.cmds as cmds
import time
import math
import traceback


# log functions

def write_converted_property_log(rpr_name, ai_name, rpr_attr, ai_attr):

	try:
		file_path = cmds.file(q=True, sceneName=True) + ".log"
		with open(file_path, 'a') as f:
			f.write(u"    property {}.{} is converted to {}.{}   \r\n".format(ai_name, ai_attr, rpr_name, rpr_attr).encode('utf-8'))
	except Exception as ex:
		pass
		#print("Error writing conversion logs. Scene is not saved")

def write_own_property_log(text):

	try:
		file_path = cmds.file(q=True, sceneName=True) + ".log"
		with open(file_path, 'a') as f:
			f.write("    {}   \r\n".format(text))
	except Exception as ex:
		pass
		#print("Error writing logs. Scene is not saved")

def start_log(ai, rpr):

	try:
		text  = u"Found node: \r\n    name: {} \r\n".format(ai).encode('utf-8')
		text += "type: {} \r\n".format(cmds.objectType(ai))
		text += u"Converting to: \r\n    name: {} \r\n".format(rpr).encode('utf-8')
		text += "type: {} \r\n".format(cmds.objectType(rpr))
		text += "Conversion details: \r\n"

		file_path = cmds.file(q=True, sceneName=True) + ".log"
		with open(file_path, 'a') as f:
			f.write(text)
	except Exception as ex:
		pass
		#print("Error writing start log. Scene is not saved")


def end_log(ai):

	try:
		text  = u"Conversion of {} is finished.\n\n \r\n".format(ai).encode('utf-8')

		file_path = cmds.file(q=True, sceneName=True) + ".log"
		with open(file_path, 'a') as f:
			f.write(text)
	except Exception as ex:
		pass
		#print("Error writing end logs. Scene is not saved")

# additional fucntions

def copyProperty(rpr_name, ai_name, rpr_attr, ai_attr):

	# full name of attribute
	ai_field = ai_name + "." + ai_attr
	rpr_field = rpr_name + "." + rpr_attr

	try:
		listConnections = cmds.listConnections(ai_field)
	except Exception:
		print(u"There is no {} field in this node. Check the field and try again. ".format(ai_field).encode('utf-8'))
		write_own_property_log(u"There is no {} field in this node. Check the field and try again. ".format(ai_field).encode('utf-8'))
		return

	try:
		if listConnections:
			obj, channel = cmds.connectionInfo(ai_field, sourceFromDestination=True).split('.')
			if cmds.objectType(obj) == "file":
				setProperty(obj, "ignoreColorSpaceFileRules", 1)
			source_name, source_attr = convertaiMaterial(obj, channel).split('.')
			connectProperty(source_name, source_attr, rpr_name, rpr_attr)
		else:
			setProperty(rpr_name, rpr_attr, getProperty(ai_name, ai_attr))
			write_converted_property_log(rpr_name, ai_name, rpr_attr, ai_attr)
	except Exception as ex:
		traceback.print_exc()
		print(u"Error while copying from {} to {}".format(ai_field, rpr_field).encode('utf-8'))


def setProperty(rpr_name, rpr_attr, value):

	# full name of attribute
	rpr_field = rpr_name + "." + rpr_attr

	try:
		if type(value) == tuple:
			cmds.setAttr(rpr_field, value[0], value[1], value[2])
		elif type(value) == str or type(value) == unicode:
			cmds.setAttr(rpr_field, value, type="string")
		else:
			cmds.setAttr(rpr_field, value)
		write_own_property_log(u"Set value {} to {}.".format(value, rpr_field).encode('utf-8'))
	except Exception as ex:
		traceback.print_exc()
		print(u"Set value {} to {} is failed. Check the values and their boundaries. ".format(value, rpr_field).encode('utf-8'))
		write_own_property_log(u"Set value {} to {} is failed. Check the values and their boundaries. ".format(value, rpr_field).encode('utf-8'))


def getProperty(material, attr):

	# full name of attribute
	field = material + "." + attr
	try:
		value = cmds.getAttr(field)
		if type(value) == list:
			value = value[0]
	except Exception as ex:
		traceback.print_exc()
		write_own_property_log(u"There is no {} field in this node. Check the field and try again. ".format(field).encode('utf-8'))
		return

	return value

def mapDoesNotExist(ai_name, ai_attr):

	# full name of attribute
	ai_field = ai_name + "." + ai_attr
	try:
		listConnections = cmds.listConnections(ai_field)
		if listConnections:
			return 0
	except Exception as ex:
		traceback.print_exc()
		write_own_property_log(u"There is no {} field in this node. Check the field and try again. ".format(ai_field).encode('utf-8'))
		return

	return 1


def connectProperty(source_name, source_attr, rpr_name, rpr_attr):

	# full name of attribute
	source = source_name + "." + source_attr
	rpr_field = rpr_name + "." + rpr_attr

	try:
		if cmds.objectType(source_name) == "file":
			setProperty(source_name, "ignoreColorSpaceFileRules", 1)
		cmds.connectAttr(source, rpr_field, force=True)
		write_own_property_log(u"Created connection from {} to {}.".format(source, rpr_field).encode('utf-8'))
	except Exception as ex:
		traceback.print_exc()
		print(u"Connection {} to {} is failed.".format(source, rpr_field).encode('utf-8'))
		write_own_property_log(u"Connection {} to {} is failed.".format(source, rpr_field).encode('utf-8'))


# dispalcement convertion
def convertDisplacement(ai_sg, rpr_name):
	try:
		displacement = cmds.listConnections(ai_sg + ".displacementShader")
		if displacement:
			displacementType = cmds.objectType(displacement[0])
			if displacementType == "displacementShader":
				displacement_file = cmds.listConnections(displacement[0], type="file")
				if displacement_file:
					setProperty(rpr_name, "displacementEnable", 1)
					connectProperty(displacement_file[0], "outColor", rpr_name, "displacementMap")
					copyProperty(rpr_name, displacement[0], "scale", "displacementMax")
			elif displacementType == "file":
				setProperty(rpr_name, "displacementEnable", 1)
				connectProperty(displacement[0], "outColor", rpr_name, "displacementMap")
	except Exception as ex:
		traceback.print_exc()
		print(u"Failed to convert displacement for {} material".format(rpr_name).encode('utf-8'))


# dispalcement convertion
def convertShadowDisplacement(ai_sg, rpr_name):
	try:
		displacement = cmds.listConnections(ai_sg + ".displacementShader")
		if displacement:
			displacementType = cmds.objectType(displacement[0])
			if displacementType == "displacementShader":
				displacement_file = cmds.listConnections(displacement[0], type="file")
				if displacement_file:
					setProperty(rpr_name, "useDispMap", 1)
					connectProperty(displacement_file[0], "outColor", rpr_name, "dispMap")
			elif displacementType == "file":
				setProperty(rpr_name, "useDispMap", 1)
				connectProperty(displacement[0], "outColor", rpr_name, "dispMap")
	except Exception as ex:
		traceback.print_exc()
		print(u"Failed to convert displacement for {} material".format(rpr_name).encode('utf-8'))


def convertaiAdd(ai, source):

	rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")

	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	setProperty(rpr, "operation", 0)
	copyProperty(rpr, ai, "inputA", "input1")
	copyProperty(rpr, ai, "inputB", "input2")
	
	# Logging to file
	end_log(ai)

	conversion_map = {
		"outColor": "out",
		"outColorR": "outX",
		"outColorG": "outY",
		"outColorB": "outZ"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiDivide(ai, source):

	rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")

	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	setProperty(rpr, "operation", 3)
	copyProperty(rpr, ai, "inputA", "input1")
	copyProperty(rpr, ai, "inputB", "input2")
	
	# Logging to file
	end_log(ai)

	conversion_map = {
		"outColor": "out",
		"outColorR": "outX",
		"outColorG": "outY",
		"outColorB": "outZ"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiSubstract(ai, source):

	rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")

	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	setProperty(rpr, "operation", 1)
	copyProperty(rpr, ai, "inputA", "input1")
	copyProperty(rpr, ai, "inputB", "input2")
	
	# Logging to file
	end_log(ai)

	conversion_map = {
		"outColor": "out",
		"outColorR": "outX",
		"outColorG": "outY",
		"outColorB": "outZ",
		"outTransparency": "out",
		"outTransparencyR": "outX",
		"outTransparencyG": "outY",
		"outTransparencyB": "outZ",
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiMultiply(ai, source):

	rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")

	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	setProperty(rpr, "operation", 2)
	copyProperty(rpr, ai, "inputA", "input1")
	copyProperty(rpr, ai, "inputB", "input2")
	
	# Logging to file
	end_log(ai)

	conversion_map = {
		"outColor": "out",
		"outColorR": "outX",
		"outColorG": "outY",
		"outColorB": "outZ"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiAbs(ai, source):

	rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")

	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	setProperty(rpr, "operation", 20)
	copyProperty(rpr, ai, "inputA", "input")
	
	# Logging to file
	end_log(ai)

	conversion_map = {
		"outColor": "out",
		"outColorR": "outX",
		"outColorG": "outY",
		"outColorB": "outZ"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiAtan(ai, source):

	rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")

	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	setProperty(rpr, "operation", 18)
	copyProperty(rpr, ai, "inputA", "x")
	copyProperty(rpr, ai, "inputB", "y")
	
	# Logging to file
	end_log(ai)

	conversion_map = {
		"outColor": "out",
		"outColorR": "outX",
		"outColorG": "outY",
		"outColorB": "outZ"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiCross(ai, source):

	rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")

	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	setProperty(rpr, "operation", 12)
	copyProperty(rpr, ai, "inputA", "input1")
	copyProperty(rpr, ai, "inputB", "input2")
	
	# Logging to file
	end_log(ai)

	conversion_map = {
		"outValue": "out",
		"outValueX": "outX",
		"outValueY": "outY",
		"outValueZ": "outZ"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiDot(ai, source):

	rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")

	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	setProperty(rpr, "operation", 11)
	copyProperty(rpr, ai, "inputA", "input1")
	copyProperty(rpr, ai, "inputB", "input2")
	
	# Logging to file
	end_log(ai)

	conversion_map = {
		"outValue": "outX"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiPow(ai, source):

	rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")

	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	setProperty(rpr, "operation", 15)
	copyProperty(rpr, ai, "inputA", "base")
	copyProperty(rpr, ai, "inputB", "exponent")
	
	# Logging to file
	end_log(ai)

	conversion_map = {
		"outColor": "out",
		"outColorR": "outX",
		"outColorG": "outY",
		"outColorB": "outZ"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiTrigo(ai, source):

	rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")

	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	function = getProperty(ai, "function")
	operation_map = {
		0: 5,
		1: 4,
		2: 6
 	}
	setProperty(rpr, "operation", operation_map[function])
	copyProperty(rpr, ai, "inputA", "input")
	
	# Logging to file
	end_log(ai)

	conversion_map = {
		"outColor": "out",
		"outColorR": "outX",
		"outColorG": "outY",
		"outColorB": "outZ"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertmultiplyDivide(ai, source):

	rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")

	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	operation = getProperty(ai, "operation")
	operation_map = {
		1: 2,
		2: 3,
		3: 15
 	}
	setProperty(rpr, "operation", operation_map[operation])
	copyProperty(rpr, ai, "inputA", "input1")
	copyProperty(rpr, ai, "inputB", "input2")
	
	# Logging to file
	end_log(ai)

	conversion_map = {
		"output": "out",
		"outputX": "outX",
		"outputY": "outY",
		"outputZ": "outZ"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertbump2d(ai, source):

	bump_type = getProperty(ai, "bumpInterp")
	if not bump_type:
		rpr = cmds.shadingNode("RPRBump", asUtility=True)
		rpr = cmds.rename(rpr, ai + "_rpr")
	else:
		rpr = cmds.shadingNode("RPRNormal", asUtility=True)
		rpr = cmds.rename(rpr, ai + "_rpr")

	# Logging to file
	start_log(ai, rpr)

	# Fields conversion

	# only file support (alpha and color connections)
	bumpConnections = cmds.listConnections(ai + ".bumpValue", type="file")
	if bumpConnections:
		connectProperty(bumpConnections[0], "outColor", rpr, "color")

	copyProperty(rpr, ai, "strength", "bumpDepth")

	# Logging to file
	end_log(ai)

	conversion_map = {
		"outNormal": "out",
		"outNormalX": "outX",
		"outNormalY": "outY",
		"outNormalZ": "outZ"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiBump2d(ai, source):

	rpr = cmds.shadingNode("RPRBump", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")
		
	# Logging to file
	start_log(ai, rpr)

	# Fields conversion

	# only file support (alpha and color connections)
	bumpConnections = cmds.listConnections(ai + ".bumpMap", type="file")
	if bumpConnections:
		connectProperty(bumpConnections[0], "outColor", rpr, "color")

	copyProperty(rpr, ai, "strength", "bumpHeight")

	# Logging to file
	end_log(ai)

	conversion_map = {
		"outValue": "out",
		"outValueX": "outX",
		"outValueY": "outY",
		"outValueZ": "outZ"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiBump3d(ai, source):

	rpr = cmds.shadingNode("RPRBump", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")
		
	# Logging to file
	start_log(ai, rpr)

	# Fields conversion

	# only file support (alpha and color connections)
	bumpConnections = cmds.listConnections(ai + ".bumpMap", type="file")
	if bumpConnections:
		connectProperty(bumpConnections[0], "outColor", rpr, "color")

	copyProperty(rpr, ai, "strength", "bumpHeight")

	# Logging to file
	end_log(ai)

	conversion_map = {
		"outValue": "out",
		"outValueX": "outX",
		"outValueY": "outY",
		"outValueZ": "outZ"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiNormalMap(ai, source):

	rpr = cmds.shadingNode("RPRNormal", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")
	
	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	if mapDoesNotExist(ai, "input"):
		copyProperty(rpr, ai, "color", "normal")
	else:
		copyProperty(rpr, ai, "color", "input")

	copyProperty(rpr, ai, "strength", "strength")

	# Logging to file
	end_log(ai)

	conversion_map = {
		"outValue": "out",
		"outValueX": "outX",
		"outValueY": "outY",
		"outValueZ": "outZ"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiVectorMap(ai, source):

	rpr = cmds.shadingNode("RPRNormal", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")
	
	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	if mapDoesNotExist(ai, "input"):
		copyProperty(rpr, ai, "color", "normal")
	else:
		copyProperty(rpr, ai, "color", "input")

	copyProperty(rpr, ai, "strength", "scale")

	# Logging to file
	end_log(ai)

	conversion_map = {
		"outValue": "out",
		"outValueX": "outX",
		"outValueY": "outY",
		"outValueZ": "outZ"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiFacingRatio(ai, source):

	rpr = cmds.shadingNode("RPRLookup", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")
		
	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	setProperty(rpr, "type", 3)

	# Logging to file
	end_log(ai)

	conversion_map = {
		"message": "out",
		"outTransparency": "out",
		"outTransparencyR": "outX",
		"outTransparencyG": "outY",
		"outTransparencyB": "outZ",
		"outValue": "outX"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiThinFilm(ai, source):

	rpr = cmds.shadingNode("RPRFresnel", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")
		
	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	ior = (getProperty(ai, "iorMedium") + getProperty(ai, "iorFilm") + getProperty(ai, "iorInternal")) / 3.0
	setProperty(rpr, "ior", ior)

	# Logging to file
	end_log(ai)

	conversion_map = {
		"outColor": "out",
		"outColorR": "out",
		"outColorG": "out",
		"outColorB": "out",
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiCurvature(ai, source):

	rpr = cmds.shadingNode("RPRAmbientOcclusion", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")
		
	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	setProperty(rpr, "side", 1)
	setProperty(rpr, "occludedColor", (1, 1, 1))
	setProperty(rpr, "unoccludedColor", (0, 0, 0))
	if mapDoesNotExist(ai, "radius"):
		setProperty(rpr, "radius", getProperty(ai, "radius") / 100)

	# Logging to file
	end_log(ai)

	conversion_map = {
		"outColor": "output",
		"outColorR": "outputR",
		"outColorG": "outputG",
		"outColorB": "outputB",
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiBlackbody(ai, source):

	rpr = cmds.shadingNode("RPRUberMaterial", asShader=True)
	rpr = cmds.rename(rpr, ai + "_rpr")
		
	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	setProperty(rpr, "diffuse", 0)
	setProperty(rpr, "emissive", 1)

	temperature = getProperty(ai, "temperature") / 100

	if temperature <= 66:
		colorR = 255
	else:
		colorR = temperature - 60
		colorR = 329.698727446 * colorR ** -0.1332047592
		if colorR < 0:
			colorR = 0
		if colorR > 255:
			colorR = 255


	if temperature <= 66:
		colorG = temperature
		colorG = 99.4708025861 * math.log(colorG) - 161.1195681661
		if colorG < 0:
			colorG = 0
		if colorG > 255:
			colorG = 255
	else:
		colorG = temperature - 60
		colorG = 288.1221695283 * colorG ** -0.0755148492
		if colorG < 0:
			colorG = 0
		if colorG > 255:
			colorG = 255


	if temperature >= 66:
		colorB = 255
	elif temperature <= 19:
		colorB = 0
	else:
		colorB = temperature - 10
		colorB = 138.5177312231 * math.log(colorB) - 305.0447927307
		if colorB < 0:
			colorB = 0
		if colorB > 255:
			colorB = 255

	colorR = colorR / 255
	colorG = colorG / 255
	colorB = colorB / 255

	setProperty(rpr, "emissiveColor", (colorR, colorG, colorB))
	copyProperty(rpr, ai, "emissiveIntensity", "intensity")

	# Logging to file
	end_log(ai)

	rpr += "." + source
	return rpr


def convertaiColorConvert(ai, source):

	from_value = getProperty(ai, "from")
	to_value = getProperty(ai, "to")

	if from_value == 0 and to_value == 1:
		objectType = "rgbToHsv"
		rpr = cmds.shadingNode("rgbToHsv", asUtility=True)
		rpr = cmds.rename(rpr, ai + "_rpr")

	elif from_value == 1 and to_value == 0:
		objectType = "hsvToRgb"
		rpr = cmds.shadingNode("hsvToRgb", asUtility=True)
		rpr = cmds.rename(rpr, ai + "_rpr")

	else:
		print("Wrong parameters for aiColorConvert conversion")
		return
		
	# Logging to file
	start_log(ai, rpr)

	if objectType == "rgbToHsv":
		copyProperty(rpr, ai, "inRgb", "input")
	elif objectType == "hsvToRgb":
		copyProperty(rpr, ai, "inHsv", "input")

	end_log(ai)

	conversion_map_rgb = {
		"outColor": "outRgb",
		"outColorR": "outRgbR",
		"outColorG": "outRgbG",
		"outColorB": "outRgbB",
	}

	conversion_map_hsv = {
		"outColor": "outHsv",
		"outColorR": "outHsvH",
		"outColorG": "outHsvS",
		"outColorB": "outHsvV",
	}

	if objectType == "rgbToHsv":
		rpr += "." + conversion_map_hsv[source]
	elif objectType == "hsvToRgb":
		rpr += "." + conversion_map_rgb[source]

	return rpr



def convertaiImage(ai, source):

	rpr = cmds.shadingNode("file", asTexture=True, isColorManaged=True)
	rpr = cmds.rename(rpr, ai + "_rpr")
	texture = cmds.shadingNode("place2dTexture", asUtility=True)

	connectProperty(texture, "coverage", rpr, "coverage")
	connectProperty(texture, "translateFrame", rpr, "translateFrame")
	connectProperty(texture, "rotateFrame", rpr, "rotateFrame")
	connectProperty(texture, "mirrorU", rpr, "mirrorU")
	connectProperty(texture, "mirrorV", rpr, "mirrorV")
	connectProperty(texture, "stagger", rpr, "stagger")
	connectProperty(texture, "wrapU", rpr, "wrapU")
	connectProperty(texture, "wrapV", rpr, "wrapV")
	connectProperty(texture, "repeatUV", rpr, "repeatUV")
	connectProperty(texture, "offset", rpr, "offset")
	connectProperty(texture, "rotateUV", rpr, "rotateUV")
	connectProperty(texture, "noiseUV", rpr, "noiseUV")
	connectProperty(texture, "vertexUvOne", rpr, "vertexUvOne")
	connectProperty(texture, "vertexUvTwo", rpr, "vertexUvTwo")
	connectProperty(texture, "vertexUvThree", rpr, "vertexUvThree")
	connectProperty(texture, "vertexCameraOne", rpr, "vertexCameraOne")
	connectProperty(texture, "outUV", rpr, "uv")
	connectProperty(texture, "outUvFilterSize", rpr, "uvFilterSize")
		
	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	setProperty(rpr, "fileTextureName", getProperty(ai, "filename"))
	setProperty(rpr, "colorSpace", getProperty(ai, "colorSpace"))
	
	copyProperty(rpr, ai, "useFrameExtension", "useFrameExtension")
	copyProperty(rpr, ai, "frameExtension", "frame")
	copyProperty(rpr, ai, "ignoreColorSpaceFileRules", "ignoreColorSpaceFileRules")

	# Logging to file
	end_log(ai)

	conversion_map = {
		"outColor": "outColor",
		"outColorR": "outColorR",
		"outColorG": "outColorG",
		"outColorB": "outColorB"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiNoise(ai, source):

	rpr = cmds.shadingNode("noise", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")

	texture = cmds.shadingNode("place2dTexture", asUtility=True)

	connectProperty(texture, "outUV", rpr, "uv")
	connectProperty(texture, "outUvFilterSize", rpr, "uvFilterSize")
		
	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	copyProperty(rpr, ai, "frequencyRatio", "octaves")
	copyProperty(rpr, ai, "frequency", "octaves")
	copyProperty(rpr, ai, "threshold", "distortion")
	copyProperty(rpr, ai, "ratio", "lacunarity")
	copyProperty(rpr, ai, "amplitude", "amplitude")
	copyProperty(rpr, ai, "defaultColor", "color1")
	copyProperty(rpr, ai, "colorGain", "color1")
	copyProperty(rpr, ai, "colorOffset", "color2")

	# Logging to file
	end_log(ai)

	rpr += "." + source
	return rpr


def convertaiCellNoise(ai, source):

	rpr = cmds.shadingNode("noise", asUtility=True)
	rpr = cmds.rename(rpr, ai + "_rpr")

	texture = cmds.shadingNode("place2dTexture", asUtility=True)

	connectProperty(texture, "outUV", rpr, "uv")
	connectProperty(texture, "outUvFilterSize", rpr, "uvFilterSize")
		
	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	copyProperty(rpr, ai, "frequencyRatio", "octaves")
	copyProperty(rpr, ai, "frequency", "octaves")
	copyProperty(rpr, ai, "ratio", "lacunarity")
	copyProperty(rpr, ai, "amplitude", "amplitude")
	copyProperty(rpr, ai, "defaultColor", "color")
	copyProperty(rpr, ai, "colorGain", "color")
	copyProperty(rpr, ai, "colorOffset", "palette")
	copyProperty(rpr, ai, "density", "density")
	copyProperty(rpr, ai, "randomness", "randomness")

	# Logging to file
	end_log(ai)

	rpr += "." + source
	return rpr


# standart utilities
def convertStandartNode(aiMaterial, source):

	try:
		for attr in cmds.listAttr(aiMaterial):
			connection = cmds.listConnections(aiMaterial + "." + attr)
			if connection:
				if cmds.objectType(connection[0]) not in ("materialInfo", "defaultShaderList", "shadingEngine") and attr not in (source, "message"):
					obj, channel = cmds.connectionInfo(aiMaterial + "." + attr, sourceFromDestination=True).split('.')
					source_name, source_attr = convertaiMaterial(obj, channel).split('.')
					connectProperty(source_name, source_attr, aiMaterial, attr)
	except Exception as ex:
		traceback.print_exc()

	return aiMaterial + "." + source


# unsupported utilities
def convertUnsupportedNode(aiMaterial, source):

	rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
	rpr = cmds.rename(rpr, aiMaterial + "_UNSUPPORTED_NODE")

	# Logging to file
	start_log(aiMaterial, rpr)

	# 2 connection save
	try:
		setProperty(rpr, "operation", 0)
		unsupported_connections = 0
		for attr in cmds.listAttr(aiMaterial):
			connection = cmds.listConnections(aiMaterial + "." + attr)
			if connection:
				if cmds.objectType(connection[0]) not in ("materialInfo", "defaultShaderList", "shadingEngine") and attr not in (source, "message"):
					if unsupported_connections < 2:
						obj, channel = cmds.connectionInfo(aiMaterial + "." + attr, sourceFromDestination=True).split('.')
						source_name, source_attr = convertaiMaterial(obj, channel).split('.')
						valueType = type(getProperty(aiMaterial, attr))
						if valueType == tuple:
							if unsupported_connections < 1:
								connectProperty(source_name, source_attr, rpr, "inputA")
							else:
								connectProperty(source_name, source_attr, rpr, "inputB")
						else:
							if unsupported_connections < 1:
								connectProperty(source_name, source_attr, rpr, "inputAX")
							else:
								connectProperty(source_name, source_attr, rpr, "inputBX")
						unsupported_connections += 1
	except Exception as ex:
		traceback.print_exc()

	# Logging to file
	end_log(aiMaterial)

	sourceType = type(getProperty(aiMaterial, source))
	if sourceType == tuple:
		rpr += ".out"
	else:
		rpr += ".outX"

	return rpr


# Create default uber material for unsupported material
def convertUnsupportedMaterial(aiMaterial, source):

	assigned = checkAssign(aiMaterial)

	# Creating new Uber material
	rprMaterial = cmds.shadingNode("RPRUberMaterial", asShader=True)
	rprMaterial = cmds.rename(rprMaterial, (aiMaterial + "_UNSUPPORTED_MATERIAL"))

	# Check assigned to any mesh
	if assigned:
		sg = rprMaterial + "SG"
		cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
		connectProperty(rprMaterial, "outColor", sg, "surfaceShader")

	# Logging to file
	start_log(aiMaterial, rprMaterial)
	
	setProperty(rprMaterial, "diffuseColor", (0, 1, 0))

	end_log(aiMaterial)

	if not assigned:
		rprMaterial += "." + source
	return rprMaterial


#######################
## aiAmbientOcclusion 
#######################

def convertaiAmbientOcclusion(aiMaterial, source):

	assigned = checkAssign(aiMaterial)
	
	if assigned:
		# Creating new Uber material
		rprMaterial = cmds.shadingNode("RPRUberMaterial", asShader=True)
		rprMaterial = cmds.rename(rprMaterial, (aiMaterial + "_rpr"))

		sg = rprMaterial + "SG"
		cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
		connectProperty(rprMaterial, "outColor", sg, "surfaceShader")

		ao = cmds.shadingNode("RPRAmbientOcclusion", asUtility=True)
		connectProperty(ao, "output", rprMaterial, "diffuseColor")
	else:
		ao = cmds.shadingNode("RPRAmbientOcclusion", asUtility=True)
		ao = cmds.rename(ao, (aiMaterial + "_rpr"))

	# Logging to file
	start_log(aiMaterial, ao)

	# Fields conversion
	copyProperty(ao, aiMaterial, "occludedColor", "white")
	copyProperty(ao, aiMaterial, "unoccludedColor", "black")
	copyProperty(ao, aiMaterial, "radius", "falloff")

	# Logging in file
	end_log(aiMaterial)

	if not assigned:
		conversion_map = {
		"outColor": "output",
		"outColorR": "outputR",
		"outColorG": "outputG",
		"outColorB": "outputB"
		}	
		rprMaterial = ao + "." + conversion_map[source]
	return rprMaterial


#######################
## aiFlat 
#######################

def convertaiFlat(aiMaterial, source):

	assigned = checkAssign(aiMaterial)
	
	# Creating new Uber material
	rprMaterial = cmds.shadingNode("RPRFlatColorMaterial", asShader=True)
	rprMaterial = cmds.rename(rprMaterial, (aiMaterial + "_rpr"))

	# Check shading engine in aiMaterial
	if assigned:
		sg = rprMaterial + "SG"
		cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
		connectProperty(rprMaterial, "outColor", sg, "surfaceShader")

	# Logging to file
	start_log(aiMaterial, rprMaterial)

	# Fields conversion
	copyProperty(rprMaterial, aiMaterial, "color", "color")

	# Logging in file
	end_log(aiMaterial)

	if not assigned:
		rprMaterial += "." + source
	return rprMaterial


#######################
## aiMixShader 
#######################

def convertaiMixShader(aiMaterial, source):

	assigned = checkAssign(aiMaterial)
	
	# Creating new Uber material
	rprMaterial = cmds.shadingNode("RPRBlendMaterial", asShader=True)
	rprMaterial = cmds.rename(rprMaterial, (aiMaterial + "_rpr"))

	# Check shading engine in aiMaterial
	if assigned:
		sg = rprMaterial + "SG"
		cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
		connectProperty(rprMaterial, "outColor", sg, "surfaceShader")

	# Logging to file
	start_log(aiMaterial, rprMaterial)

	# Fields conversion
	copyProperty(rprMaterial, aiMaterial, "color0", "shader1")
	copyProperty(rprMaterial, aiMaterial, "color1", "shader2")
	copyProperty(rprMaterial, aiMaterial, "weight", "mix")

	# Logging in file
	end_log(aiMaterial)

	if not assigned:
		rprMaterial += "." + source
	return rprMaterial


#######################
## aiStandardSurface 
#######################

def convertaiStandardSurface(aiMaterial, source):

	assigned = checkAssign(aiMaterial)
	
	# Creating new Uber material
	rprMaterial = cmds.shadingNode("RPRUberMaterial", asShader=True)
	rprMaterial = cmds.rename(rprMaterial, (aiMaterial + "_rpr"))

	# Check shading engine in aiMaterial
	if assigned:
		sg = rprMaterial + "SG"
		cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
		connectProperty(rprMaterial, "outColor", sg, "surfaceShader")

		ai_materialSG = cmds.listConnections(aiMaterial, type="shadingEngine")[0]
		convertDisplacement(ai_materialSG, rprMaterial)

	# Enable properties, which are default in Arnold
	defaultEnable(rprMaterial, aiMaterial, "diffuse", "base")
	defaultEnable(rprMaterial, aiMaterial, "reflections", "specular")
	defaultEnable(rprMaterial, aiMaterial, "refraction", "transmission")
	defaultEnable(rprMaterial, aiMaterial, "sssEnable", "subsurface")
	defaultEnable(rprMaterial, aiMaterial, "emissive", "emission")
	defaultEnable(rprMaterial, aiMaterial, "clearCoat", "coat")

	# Logging to file
	start_log(aiMaterial, rprMaterial)

	# Fields conversion
	copyProperty(rprMaterial, aiMaterial, "diffuseColor", "baseColor")
	copyProperty(rprMaterial, aiMaterial, "diffuseWeight", "base")
	copyProperty(rprMaterial, aiMaterial, "diffuseRoughness", "diffuseRoughness")

	copyProperty(rprMaterial, aiMaterial, "reflectColor", "specularColor")
	copyProperty(rprMaterial, aiMaterial, "reflectWeight", "specular")
	copyProperty(rprMaterial, aiMaterial, "reflectRoughness", "specularRoughness")
	copyProperty(rprMaterial, aiMaterial, "reflectAnisotropy", "specularAnisotropy")
	copyProperty(rprMaterial, aiMaterial, "reflectAnisotropyRotation", "specularRotation")
	copyProperty(rprMaterial, aiMaterial, "reflectIOR", "specularIOR")

	metalness = getProperty(aiMaterial, "metalness")
	if metalness:
		setProperty(rprMaterial, "reflections", 1)
		setProperty(rprMaterial, "diffuse", 1)
		setProperty(rprMaterial, "reflectMetalMaterial", 1)
		setProperty(rprMaterial, "reflectWeight", 1)
		copyProperty(rprMaterial, aiMaterial, "reflectMetalness", "metalness")
		copyProperty(rprMaterial, aiMaterial, "diffuseColor", "baseColor")
		copyProperty(rprMaterial, aiMaterial, "reflectColor", "baseColor")

	copyProperty(rprMaterial, aiMaterial, "refractColor", "transmissionColor")
	copyProperty(rprMaterial, aiMaterial, "refractWeight", "transmission")
	copyProperty(rprMaterial, aiMaterial, "refractRoughness", "transmissionExtraRoughness")
	setProperty(rprMaterial, "refractThinSurface", getProperty(aiMaterial, "thinWalled"))

	copyProperty(rprMaterial, aiMaterial, "volumeScatter", "subsurfaceColor")
	copyProperty(rprMaterial, aiMaterial, "sssWeight", "subsurface")
	copyProperty(rprMaterial, aiMaterial, "backscatteringWeight", "subsurface")
	copyProperty(rprMaterial, aiMaterial, "subsurfaceRadius", "subsurfaceRadius")

	subsurface = getProperty(aiMaterial, "subsurface")
	if subsurface:
		setProperty(rprMaterial, "diffuse", 1)
		setProperty(rprMaterial, "diffuseWeight", 1)
		setProperty(rprMaterial, "separateBackscatterColor", 0)
		setProperty(rprMaterial, "multipleScattering", 0)
		setProperty(rprMaterial, "backscatteringWeight", 0.75)

	copyProperty(rprMaterial, aiMaterial, "coatColor", "coatColor")
	copyProperty(rprMaterial, aiMaterial, "coatTransmissionColor", "coatColor")
	copyProperty(rprMaterial, aiMaterial, "coatWeight", "coat")
	copyProperty(rprMaterial, aiMaterial, "coatRoughness", "coatRoughness")
	copyProperty(rprMaterial, aiMaterial, "coatIor", "coatIOR")
	copyProperty(rprMaterial, aiMaterial, "coatNormal", "coatNormal")
	setProperty(rprMaterial, "coatThickness", 1.5)

	copyProperty(rprMaterial, aiMaterial, "emissiveColor", "emissionColor")
	copyProperty(rprMaterial, aiMaterial, "emissiveWeight", "emission")

	if getProperty(aiMaterial, "opacity") != (1, 1, 1):
		if mapDoesNotExist(aiMaterial, "opacity"):
			transparency = 1 - max(getProperty(aiMaterial, "opacity"))
			setProperty(rprMaterial, "transparencyLevel", transparency)
		else:
			arithmetic = cmds.shadingNode("RPRArithmetic", asUtility=True)
			setProperty(arithmetic, "operation", 1)
			setProperty(arithmetic, "inputA", (1, 1, 1))
			copyProperty(arithmetic, aiMaterial, "inputB", "opacity")
			connectProperty(arithmetic, "outX", rprMaterial, "transparencyLevel")
		setProperty(rprMaterial, "transparencyEnable", 1)

	bumpConnections = cmds.listConnections(aiMaterial + ".normalCamera")
	if bumpConnections:
		setProperty(rprMaterial, "normalMapEnable", 1)
		copyProperty(rprMaterial, aiMaterial, "normalMap", "normalCamera")
		if getProperty(aiMaterial, "base"):
			copyProperty(rprMaterial, aiMaterial, "diffuseNormal", "normalCamera")
		if getProperty(aiMaterial, "specular"):
			copyProperty(rprMaterial, aiMaterial, "reflectNormal", "normalCamera")
		if getProperty(aiMaterial, "transmission"):
			copyProperty(rprMaterial, aiMaterial, "refractNormal", "normalCamera")
		if getProperty(aiMaterial, "coat"):
			copyProperty(rprMaterial, aiMaterial, "coatNormal", "normalCamera")
	
	# Logging in file
	end_log(aiMaterial)

	if not assigned:
		rprMaterial += "." + source
	return rprMaterial


#######################
## aiCarPaint 
#######################

def convertaiCarPaint(aiMaterial, source):

	assigned = checkAssign(aiMaterial)
	
	# Creating new Uber material
	rprMaterial = cmds.shadingNode("RPRUberMaterial", asShader=True)
	rprMaterial = cmds.rename(rprMaterial, (aiMaterial + "_rpr"))

	# Check shading engine in aiMaterial
	if assigned:
		sg = rprMaterial + "SG"
		cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
		connectProperty(rprMaterial, "outColor", sg, "surfaceShader")

	# Enable properties, which are default in Arnold
	defaultEnable(rprMaterial, aiMaterial, "diffuse", "base")
	defaultEnable(rprMaterial, aiMaterial, "reflections", "specular")
	defaultEnable(rprMaterial, aiMaterial, "clearCoat", "coat")

	# Logging to file
	start_log(aiMaterial, rprMaterial)

	# Fields conversion
	copyProperty(rprMaterial, aiMaterial, "diffuseColor", "baseColor")
	copyProperty(rprMaterial, aiMaterial, "diffuseWeight", "base")
	copyProperty(rprMaterial, aiMaterial, "diffuseRoughness", "baseRoughness")

	copyProperty(rprMaterial, aiMaterial, "reflectColor", "specularColor")
	copyProperty(rprMaterial, aiMaterial, "reflectWeight", "specular")
	copyProperty(rprMaterial, aiMaterial, "reflectRoughness", "specularRoughness")
	copyProperty(rprMaterial, aiMaterial, "reflectIOR", "specularIOR")

	copyProperty(rprMaterial, aiMaterial, "coatColor", "coatColor")
	copyProperty(rprMaterial, aiMaterial, "coatWeight", "coat")
	copyProperty(rprMaterial, aiMaterial, "coatRoughness", "coatRoughness")
	copyProperty(rprMaterial, aiMaterial, "coatIor", "coatIOR")

	bumpConnections = cmds.listConnections(aiMaterial + ".coatNormal")
	if bumpConnections:
		setProperty(rprMaterial, "normalMapEnable", 1)
		copyProperty(rprMaterial, aiMaterial, "normalMap", "coatNormal")
		setProperty(rprMaterial, "useShaderNormal", 1)
		setProperty(rprMaterial, "reflectUseShaderNormal", 1)
		setProperty(rprMaterial, "refractUseShaderNormal", 1)
		setProperty(rprMaterial, "coatUseShaderNormal", 1)

	# Logging in file
	end_log(aiMaterial)

	if not assigned:
		rprMaterial += "." + source
	return rprMaterial


#######################
## aiShadowMatte 
#######################

def convertaiShadowMatte(aiMaterial, source):

	assigned = checkAssign(aiMaterial)
	
	# Creating new Uber material
	rprMaterial = cmds.shadingNode("RPRShadowCatcherMaterial", asShader=True)
	rprMaterial = cmds.rename(rprMaterial, (aiMaterial + "_rpr"))

	# Check shading engine in aiMaterial
	if assigned:
		sg = rprMaterial + "SG"
		cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
		connectProperty(rprMaterial, "outColor", sg, "surfaceShader")

		ai_materialSG = cmds.listConnections(aiMaterial, type="shadingEngine")[0]
		convertShadowDisplacement(ai_materialSG, rprMaterial)

	# Logging to file
	start_log(aiMaterial, rprMaterial)

	# Fields conversion
	copyProperty(rprMaterial, aiMaterial, "shadowColor", "shadowColor")

	if mapDoesNotExist(aiMaterial, "shadowOpacity"):
		transparency = 1 - getProperty(aiMaterial, "shadowOpacity")
		setProperty(rprMaterial, "shadowTransp", transparency)
	else:
		arithmetic = cmds.shadingNode("RPRArithmetic", asUtility=True)
		setProperty(arithmetic, "operation", 1)
		setProperty(arithmetic, "inputA", (1, 1, 1))
		copyProperty(arithmetic, aiMaterial, "inputBX", "shadowOpacity")
		connectProperty(arithmetic, "outX", rprMaterial, "shadowTransp")

	copyProperty(rprMaterial, aiMaterial, "bgColor", "backgroundColor")

	# Logging in file
	end_log(aiMaterial)

	if not assigned:
		rprMaterial += "." + source
	return rprMaterial


#######################
## aiStandardVolume 
#######################

def convertaiStandardVolume(aiMaterial, source):

	assigned = checkAssign(aiMaterial)
	
	# Creating new Uber material
	rprMaterial = cmds.shadingNode("RPRVolumeMaterial", asShader=True)
	rprMaterial = cmds.rename(rprMaterial, (aiMaterial + "_rpr"))

	# Check shading engine in aiMaterial
	if assigned:
		sg = rprMaterial + "SG"
		cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
		connectProperty(rprMaterial, "outColor", sg, "surfaceShader")

	# Logging to file
	start_log(aiMaterial, rprMaterial)

	# Fields conversion
	copyProperty(rprMaterial, aiMaterial, "scatterColor", "scatterColor")
	copyProperty(rprMaterial, aiMaterial, "emissionColor", "emissionColor")
	copyProperty(rprMaterial, aiMaterial, "transmissionColor", "transparent")
	copyProperty(rprMaterial, aiMaterial, "density", "density")

	# Logging in file
	end_log(aiMaterial)

	if not assigned:
		rprMaterial += "." + source
	return rprMaterial


def convertaiSkyDomeLight(dome_light):

	if cmds.objExists("RPRIBL"):
		iblShape = "RPRIBLShape"
		iblTransform = "RPRIBL"
	else:
		# create IBL node
		iblShape = cmds.createNode("RPRIBL", n="RPRIBLShape")
		iblTransform = cmds.listRelatives(iblShape, p=True)[0]
		setProperty(iblTransform, "scaleX", 1001.25663706144)
		setProperty(iblTransform, "scaleY", 1001.25663706144)
		setProperty(iblTransform, "scaleZ", 1001.25663706144)

	# Logging to file 
	start_log(dome_light, iblShape)
  
	# display IBL option
	exposure = getProperty(dome_light, "exposure")
	intensity = getProperty(dome_light, "intensity")
	setProperty(iblShape, "intensity", intensity * 2 ** exposure)

	# Copy properties from ai dome light
	domeTransform = cmds.listRelatives(dome_light, p=True)[0]
	setProperty(iblTransform, "rotateY", getProperty(domeTransform, "rotateY") + 180)
	
	file = cmds.listConnections(dome_light + ".color")
	if file:
		setProperty(iblTransform, "filePath", getProperty(file[0], "fileTextureName"))
		   
	# Logging to file
	end_log(dome_light)  


def convertaiSky(sky):

	if cmds.objExists("RPRIBL"):
		iblShape = "RPRIBLShape"
		iblTransform = "RPRIBL"
	else:
		# create IBL node
		iblShape = cmds.createNode("RPRIBL", n="RPRIBLShape")
		iblTransform = cmds.listRelatives(iblShape, p=True)[0]
		setProperty(iblTransform, "scaleX", 1001.25663706144)
		setProperty(iblTransform, "scaleY", 1001.25663706144)
		setProperty(iblTransform, "scaleZ", 1001.25663706144)

	# Logging to file 
	start_log(sky, iblShape)
  
	# Copy properties from ai dome light
	setProperty(iblShape, "intensity", getProperty(sky, "intensity"))

	file = cmds.listConnections(sky + ".color")
	if file:
		setProperty(iblTransform, "filePath", getProperty(file[0], "fileTextureName"))
	 
	# Logging to file
	end_log(sky)  


def convertaiPhysicalSky(sky):
	
	if cmds.objExists("RPRSky"):
		skyNode = "RPRSkyShape"
	else:
		# create RPRSky node
		skyNode = cmds.createNode("RPRSky", n="RPRSkyShape")
  
	# Logging to file
	start_log(sky, skyNode)

	# Copy properties from rsPhysicalSky
	setProperty(skyNode, "turbidity", getProperty(sky, "turbidity"))
	setProperty(skyNode, "intensity", getProperty(sky, "intensity"))
	setProperty(skyNode, "altitude", getProperty(sky, "elevation"))
	setProperty(skyNode, "azimuth", getProperty(sky, "azimuth"))
	setProperty(skyNode, "groundColor", getProperty(sky, "groundAlbedo"))
	setProperty(skyNode, "sunDiskSize", getProperty(sky, "sunSize"))

	# Logging to file
	end_log(sky)  


def convertaiPhotometricLight(ai_light):

	# Arnold light transform
	splited_name = ai_light.split("|")
	aiTransform = "|".join(splited_name[0:-1])
	group = "|".join(splited_name[0:-2])

	if cmds.objExists(aiTransform + "_rpr"):
		rprTransform = aiTransform + "_rpr"
		rprLightShape = cmds.listRelatives(rprTransform)[0]
	else: 
		rprLightShape = cmds.createNode("RPRIES", n="RPRIESLight")
		rprLightShape = cmds.rename(rprLightShape, splited_name[-1] + "_rpr")
		rprTransform = cmds.listRelatives(rprLightShape, p=True)[0]
		rprTransform = cmds.rename(rprTransform, splited_name[-2] + "_rpr")
		rprLightShape = cmds.listRelatives(rprTransform)[0]

		if group:
			cmds.parent(rprTransform, group)

		rprTransform = group + "|" + rprTransform
		rprLightShape = rprTransform + "|" + rprLightShape

	# Logging to file 
	start_log(ai_light, rprLightShape)

	# Copy properties from rsLight
	copyProperty(rprTransform, aiTransform, "translateX", "translateX")
	copyProperty(rprTransform, aiTransform, "translateY", "translateY")
	copyProperty(rprTransform, aiTransform, "translateZ", "translateZ")
	setProperty(rprTransform, "rotateX", getProperty(aiTransform, "rotateX") + 90)
	copyProperty(rprTransform, aiTransform, "rotateY", "rotateY")
	copyProperty(rprTransform, aiTransform, "rotateZ", "rotateZ")
	copyProperty(rprTransform, aiTransform, "scaleX", "scaleX")
	copyProperty(rprTransform, aiTransform, "scaleY", "scaleY")
	copyProperty(rprTransform, aiTransform, "scaleZ", "scaleZ")

	copyProperty(rprLightShape, ai_light, "color", "color")

	intensity = getProperty(ai_light, "intensity")
	exposure = getProperty(ai_light, "exposure")
	setProperty(rprLightShape, "intensity", intensity * (exposure + 5) / 500)

	setProperty(rprLightShape, "iesFile", getProperty(ai_light, "aiFilename"))
	
	# Logging to file
	end_log(ai_light) 


def convertaiAreaLight(ai_light):

	splited_name = ai_light.split("|")
	aiTransform = "|".join(splited_name[0:-1])
	group = "|".join(splited_name[0:-2])

	# Arnold light transform
	if cmds.objExists(aiTransform + "_rpr"):
		rprTransform = aiTransform + "_rpr"
		rprLightShape = cmds.listRelatives(rprTransform)[0]
	else: 
		rprLightShape = cmds.createNode("RPRPhysicalLight", n="RPRPhysicalLightShape")
		rprLightShape = cmds.rename(rprLightShape, splited_name[-1] + "_rpr")
		rprTransform = cmds.listRelatives(rprLightShape, p=True)[0]
		rprTransform = cmds.rename(rprTransform, splited_name[-2] + "_rpr")
		rprLightShape = cmds.listRelatives(rprTransform)[0]

		if group:
			cmds.parent(rprTransform, group)

		rprTransform = group + "|" + rprTransform
		rprLightShape = rprTransform + "|" + rprLightShape

	# Logging to file 
	start_log(ai_light, rprLightShape)

	# Copy properties from aiLight
	copyProperty(rprLightShape, ai_light, "lightIntensity", "intensity")
	copyProperty(rprLightShape, ai_light, "colorPicker", "color")
	copyProperty(rprLightShape, ai_light, "luminousEfficacy", "exposure")
	
	copyProperty(rprTransform, aiTransform, "translateX", "translateX")
	copyProperty(rprTransform, aiTransform, "translateY", "translateY")
	copyProperty(rprTransform, aiTransform, "translateZ", "translateZ")
	copyProperty(rprTransform, aiTransform, "rotateX", "rotateX")
	copyProperty(rprTransform, aiTransform, "rotateY", "rotateY")
	copyProperty(rprTransform, aiTransform, "rotateZ", "rotateZ")
	copyProperty(rprTransform, aiTransform, "scaleX", "scaleX")
	copyProperty(rprTransform, aiTransform, "scaleY", "scaleY")
	copyProperty(rprTransform, aiTransform, "scaleZ", "scaleZ")

	# Logging to file
	end_log(ai_light)  


def convertaiMeshLight(ai_light):

	# Arnold light transform
	splited_name = ai_light.split("|")
	aiTransform = "|".join(splited_name[0:-1])
	group = "|".join(splited_name[0:-2])

	if cmds.objExists(aiTransform + "_rpr"):
		rprTransform = aiTransform + "_rpr"
		rprLightShape = cmds.listRelatives(rprTransform)[0]
	else: 
		rprLightShape = cmds.createNode("RPRPhysicalLight", n="RPRPhysicalLightShape")
		rprLightShape = cmds.rename(rprLightShape, splited_name[-1] + "_rpr")
		rprTransform = cmds.listRelatives(rprLightShape, p=True)[0]
		rprTransform = cmds.rename(rprTransform, splited_name[-2] + "_rpr")
		rprLightShape = cmds.listRelatives(rprTransform)[0]

		if group:
			cmds.parent(rprTransform, group)

		rprTransform = group + "|" + rprTransform
		rprLightShape = rprTransform + "|" + rprLightShape

	# Logging to file 
	start_log(ai_light, rprLightShape)

	# Copy properties from aiLight
	setProperty(rprLightShape, "lightType", 0)
	setProperty(rprLightShape, "areaLightShape", 4)

	copyProperty(rprLightShape, ai_light, "lightIntensity", "intensity")
	copyProperty(rprLightShape, ai_light, "colorPicker", "color")
	copyProperty(rprLightShape, ai_light, "luminousEfficacy", "aiExposure")
	if getProperty(ai_light, "aiUseColorTemperature"):
		setProperty(rprLightShape, "colorMode", 1)
	copyProperty(rprLightShape, ai_light, "temperature", "aiColorTemperature")
	copyProperty(rprLightShape, ai_light, "shadowsEnabled", "aiCastShadows")
	copyProperty(rprLightShape, ai_light, "shadowsSoftness", "aiShadowDensity")

	copyProperty(rprTransform, aiTransform, "translateX", "translateX")
	copyProperty(rprTransform, aiTransform, "translateY", "translateY")
	copyProperty(rprTransform, aiTransform, "translateZ", "translateZ")
	copyProperty(rprTransform, aiTransform, "rotateX", "rotateX")
	copyProperty(rprTransform, aiTransform, "rotateY", "rotateY")
	copyProperty(rprTransform, aiTransform, "rotateZ", "rotateZ")
	copyProperty(rprTransform, aiTransform, "scaleX", "scaleX")
	copyProperty(rprTransform, aiTransform, "scaleY", "scaleY")
	copyProperty(rprTransform, aiTransform, "scaleZ", "scaleZ")

	try:
		light_mesh = cmds.listConnections(ai_light, type="mesh")[1]
		cmds.delete(ai_light)
		cmds.delete(aiTransform)
		setProperty(rprLightShape, "areaLightSelectingMesh", 1)
		cmds.select(light_mesh)
		#setProperty(rprLightShape, "areaLightMeshSelectedName", light_mesh)
	except Exception as ex:
		traceback.print_exc()
		print("Failed to convert mesh in Physical light")

	# Logging to file
	end_log(ai_light)


def convertaiAtmosphere(aiAtmosphere):

	# Creating new Volume material
	rprMaterial = cmds.shadingNode("RPRVolumeMaterial", asShader=True)
	rprMaterial = cmds.rename(rprMaterial, (aiAtmosphere + "_rpr"))
	
	sg = rprMaterial + "SG"
	cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
	connectProperty(rprMaterial, "outColor", sg, "volumeShader")

	# create sphere
	cmds.polySphere(n="Volume")
	setProperty("Volume", "scaleX", 2000)
	setProperty("Volume", "scaleY", 2000)
	setProperty("Volume", "scaleZ", 2000)

	# assign material
	cmds.select("Volume")
	cmds.sets(e=True, forceElement=sg)

	# Logging to file 
	start_log(aiAtmosphere, rprMaterial) 

	# Fields conversion
	setProperty(rprMaterial, "multiscatter", 0)

	aiAtmosphereType = cmds.objectType(aiAtmosphere)
	if aiAtmosphereType == "aiFog":
		copyProperty(rprMaterial, aiAtmosphere, "emissionColor", "color")
		avg_color = getProperty(aiAtmosphere, "color") / 3.0
		setProperty(rprMaterial, "density", avg_color)
	elif aiAtmosphereType == "aiAtmosphereVolume":
		copyProperty(rprMaterial, aiAtmosphere, "density", "density")
		copyProperty(rprMaterial, aiAtmosphere, "scatterColor", "rgbDensity")
		copyProperty(rprMaterial, aiAtmosphere, "transmissionColor", "rgbDensity")
		copyProperty(rprMaterial, aiAtmosphere, "scatteringDirection", "eccentricity")

		density = getProperty(aiAtmosphere, "scatteringAmount") / 10
		setProperty(rprMaterial, "density", density)
	
	# Logging to file
	end_log(aiAtmosphere)  


# Convert material. Returns new material name.
def convertaiMaterial(aiMaterial, source):

	ai_type = cmds.objectType(aiMaterial)

	conversion_func = {
		"aiAmbientOcclusion": convertaiAmbientOcclusion,
		"aiCarPaint": convertaiCarPaint,
		"aiFlat": convertaiFlat,
		"aiLayerShader": convertUnsupportedMaterial,
		"aiMatte": convertUnsupportedMaterial,
		"aiMixShader": convertaiMixShader,
		"aiPassthrough": convertUnsupportedMaterial,
		"aiRaySwitch": convertUnsupportedMaterial,
		"aiShadowMatte": convertaiShadowMatte,
		"aiStandardHair": convertUnsupportedMaterial,
		"aiStandardSurface": convertaiStandardSurface,
		"aiSwitch": convertUnsupportedMaterial,
		"aiToon": convertUnsupportedMaterial,
		"aiTwoSided": convertUnsupportedMaterial,
		"aiUtility": convertUnsupportedMaterial,
		"aiWireframe": convertUnsupportedMaterial,
		"aiStandardVolume": convertaiStandardVolume,
		##utilities
		"bump2d": convertbump2d,
		"aiBump2d": convertaiBump2d,
		"aiBump3d": convertaiBump3d,
		"aiNormalMap": convertaiNormalMap,
		"aiVectorMap": convertaiVectorMap,
		"aiAdd": convertaiAdd,
		"aiMultiply": convertaiMultiply,
		"aiDivide": convertaiDivide,
		"aiSubtract": convertaiSubstract,
		"aiAbs": convertaiAbs,
		"aiAtan": convertaiAtan,
		"aiCross": convertaiCross,
		"aiDot": convertaiDot,
		"aiPow": convertaiPow,
		"aiTrigo": convertaiTrigo,
		"aiImage": convertaiImage,
		"aiFacingRatio": convertaiFacingRatio,
		"aiThinFilm": convertaiThinFilm,
		"aiColorConvert": convertaiColorConvert,
		"aiCellNoise": convertaiCellNoise,
		"aiNoise": convertaiNoise,
		"aiBlackbody": convertaiBlackbody,
		"aiCurvature": convertaiCurvature,
		"multiplyDivide": convertmultiplyDivide
	}

	if ai_type in conversion_func:
		rpr = conversion_func[ai_type](aiMaterial, source)
	else:
		if isArnoldType(aiMaterial):
			rpr = convertUnsupportedNode(aiMaterial, source)
		else:
			rpr = convertStandartNode(aiMaterial, source)

	return rpr


# Convert light. Returns new light name.
def convertLight(light):

	ai_type = cmds.objectType(light)

	conversion_func = {
		"aiAreaLight": convertaiAreaLight,
		"aiMeshLight": convertaiMeshLight,
		"aiPhotometricLight": convertaiPhotometricLight,
		"aiSkyDomeLight": convertaiSkyDomeLight,
	}

	conversion_func[ai_type](light)


def isArnoldType(obj):

	if cmds.objExists(obj):
		objType = cmds.objectType(obj)
		if objType.startswith("ai"):
			return 1
	return 0


def cleanScene():

	listMaterials= cmds.ls(materials=True)
	for material in listMaterials:
		if isArnoldType(material):
			shEng = cmds.listConnections(material, type="shadingEngine")
			try:
				cmds.delete(shEng[0])
				cmds.delete(material)
			except Exception as ex:
				traceback.print_exc()

	listLights = cmds.ls(l=True, type=["aiAreaLight", "aiMeshLight", "aiPhotometricLight", "aiSkyDomeLight"])
	for light in listLights:
		transform = cmds.listRelatives(light, p=True)[0]
		try:
			cmds.delete(light)
			cmds.delete(transform)
		except Exception as ex:
			traceback.print_exc()

	listObjects = cmds.ls(l=True)
	for obj in listObjects:
		if isArnoldType(object):
			try:
				cmds.delete(obj)
			except Exception as ex:
				traceback.print_exc()


def checkAssign(material):

	if isArnoldType(material):
		materialSG = cmds.listConnections(material, type="shadingEngine")
		if materialSG:
			cmds.hyperShade(objects=material)
			assigned = cmds.ls(sl=True)
			if assigned:
				return 1
	return 0


def defaultEnable(RPRmaterial, aiMaterial, enable, value):

	weight = getProperty(aiMaterial, value)
	if weight > 0:
		setProperty(RPRmaterial, enable, 1)
	else:
		setProperty(RPRmaterial, enable, 0)


def convertScene():

	# Check plugins
	if not cmds.pluginInfo("mtoa", q=True, loaded=True):
		cmds.loadPlugin("mtoa")

	if not cmds.pluginInfo("RadeonProRender", q=True, loaded=True):
		cmds.loadPlugin("RadeonProRender")

	# Convert aiAtmosphere
	env = cmds.ls(type=("aiAtmosphereVolume", "aiFog"))
	if env:
		try:
			convertaiAtmosphere(env[0])
		except Exception as ex:
			traceback.print_exc()
			print("Error while converting Atmosphere. ")

	# Convert ArnoldPhysicalSky
	sky = cmds.ls(type=("aiPhysicalSky", "aiSky"))
	if sky:
		try:
			sky_type = cmds.objectType(sky[0])
			conversion_func_sky = {
				"aiPhysicalSky": convertaiPhysicalSky,
				"aiSky": convertaiSky
			}
			conversion_func_sky[sky_type](sky[0])
		except Exception as ex:
			traceback.print_exc()
			print("Error while converting physical sky. \n")

	
	# Get all lights from scene
	listLights = cmds.ls(l=True, type=["aiAreaLight", "aiMeshLight", "aiPhotometricLight", "aiSkyDomeLight"])

	# Convert lights
	for light in listLights:
		try:
			convertLight(light)
		except Exception as ex:
			traceback.print_exc()
			print("Error while converting {} light. \n".format(light))
		

	# Get all materials from scene
	listMaterials = cmds.ls(materials=True)
	materialsDict = {}
	for each in listMaterials:
		if checkAssign(each):
			try:
				materialsDict[each] = convertaiMaterial(each, "")
			except Exception as ex:
				traceback.print_exc()
				print("Error while converting {}".format(each))

	for ai, rpr in materialsDict.items():
		try:
			cmds.hyperShade(objects=ai)
			rpr_sg = cmds.listConnections(rpr, type="shadingEngine")[0]
			cmds.sets(e=True, forceElement=rpr_sg)
		except Exception as ex:
			print("Error while converting {} material. \n".format(ai))
	
	setProperty("defaultRenderGlobals", "currentRenderer", "FireRender")
	setProperty("defaultRenderGlobals", "imageFormat", 8)
	# setProperty("RadeonProRenderGlobals", "applyGammaToMayaViews", 1)
	
	matteShadowCatcher = cmds.ls(materials=True, type="aiShadowMatte")
	if matteShadowCatcher:
		try:
			setProperty("RadeonProRenderGlobals", "aovOpacity", 1)
			setProperty("RadeonProRenderGlobals", "aovBackground", 1)
			setProperty("RadeonProRenderGlobals", "aovShadowCatcher", 1)
		except Exception as ex:
			traceback.print_exc()



def auto_launch():
	convertScene()
	cleanScene()

def manual_launch():
	print("Convertion start!")
	startTime = 0
	testTime = 0
	startTime = time.time()
	convertScene()
	testTime = time.time() - startTime
	print("Convertion finished! Time: " + str(testTime))

	response = cmds.confirmDialog(title="Convertation finished",
							  message=("Total time: " + str(testTime) + "\nDelete all arnold instances?"),
							  button=["Yes", "No"],
							  defaultButton="Yes",
							  cancelButton="No",
							  dismissString="No")

	if response == "Yes":
		cleanScene()


def onMayaDroppedPythonFile(empty):
	manual_launch()

if __name__ == "__main__":
	manual_launch()
