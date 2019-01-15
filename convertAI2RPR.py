
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

'''

import maya.mel as mel
import maya.cmds as cmds
import time
import math


# log functions

def write_converted_property_log(rpr_name, ai_name, rpr_attr, ai_attr):

	try:
		file_path = cmds.file(q=True, sceneName=True) + ".log"
		with open(file_path, 'a') as f:
			f.write("    property " + ai_name + "." + ai_attr + " converted to " + rpr_name + "." + rpr_attr + "   \r\n")
	except Exception:
		print("Error writing logs. Scene is not saved")

def write_own_property_log(text):

	try:
		file_path = cmds.file(q=True, sceneName=True) + ".log"
		with open(file_path, 'a') as f:
			f.write("    " + text + "   \r\n")
	except Exception:
		print("Error writing logs. Scene is not saved")

def start_log(ai, rpr):

	try:
		text  = "Found node: \r\n    name: " + ai + "\r\n"
		text += "type: " + cmds.objectType(ai) + "\r\n"
		text += "Converting to: \r\n    name: " + rpr + "\r\n"
		text += "type: " + cmds.objectType(rpr) + "\r\n"
		text += "Conversion details: \r\n"

		file_path = cmds.file(q=True, sceneName=True) + ".log"
		with open(file_path, 'a') as f:
			f.write(text)
	except Exception:
		print("Error writing logs. Scene is not saved")


def end_log(ai):

	try:
		text  = "Conversion of " + ai + " is finished.\n\n"
		text += "\r\n"

		file_path = cmds.file(q=True, sceneName=True) + ".log"
		with open(file_path, 'a') as f:
			f.write(text)
	except Exception:
		print("Error writing logs. Scene is not saved")

# additional fucntions

def copyProperty(rpr_name, ai_name, rpr_attr, ai_attr):

	# full name of attribute
	ai_field = ai_name + "." + ai_attr
	rpr_field = rpr_name + "." + rpr_attr

	try:
		listConnections = cmds.listConnections(ai_field)
	except Exception:
		print("There is no {} field in this node. Check the field and try again. ".format(ai_field))
		write_own_property_log("There is no {} field in this node. Check the field and try again. ".format(ai_field))
		return

	if listConnections:
		obj, channel = cmds.connectionInfo(ai_field, sourceFromDestination=True).split('.')
		if cmds.objectType(obj) == "file":
			setProperty(obj, "ignoreColorSpaceFileRules", 1)
		source_name, source_attr = convertaiMaterial(obj, channel).split('.')
		connectProperty(source_name, source_attr, rpr_name, rpr_attr)
	else:
		setProperty(rpr_name, rpr_attr, getProperty(ai_name, ai_attr))
		write_converted_property_log(rpr_name, ai_name, rpr_attr, ai_attr)


def setProperty(rpr_name, rpr_attr, value):

	# full name of attribute
	rpr_field = rpr_name + "." + rpr_attr

	if type(value) == tuple:
		try:
			cmds.setAttr(rpr_field, value[0], value[1], value[2])
			write_own_property_log("Set value {} to {}.".format(value, rpr_field))
		except Exception:
			print("Set value {} to {} is failed. Check the values and their boundaries. ".format(value, rpr_field))
			write_own_property_log("Set value {} to {} is failed. Check the values and their boundaries. ".format(value, rpr_field))
	else:
		try:
			cmds.setAttr(rpr_field, value)
			write_own_property_log("Set value {} to {}.".format(value, rpr_field))
		except Exception:
			print("Set value {} to {} is failed. Check the values and their boundaries. ".format(value, rpr_field))
			write_own_property_log("Set value {} to {} is failed. Check the values and their boundaries. ".format(value, rpr_field))


def getProperty(material, attr):

	# full name of attribute
	field = material + "." + attr
	try:
		value = cmds.getAttr(field)
		if type(value) == list:
			value = value[0]
	except Exception as ex:
		print(ex)
		write_own_property_log("There is no {} field in this node. Check the field and try again. ".format(field))
		return

	return value

def mapDoesNotExist(rpr_name, ai_name, rpr_attr, ai_attr):

	# full name of attribute
	ai_field = ai_name + "." + ai_attr
	rpr_field = rpr_name + "." + rpr_attr

	try:
		listConnections = cmds.listConnections(ai_field)
	except Exception as ex:
		print(ex)
		write_own_property_log("There is no {} field in this node. Check the field and try again. ".format(ai_field))
		return

	if listConnections:
		source = cmds.connectionInfo(ai_field, sourceFromDestination=True)
		print("Connection {} to {} isn't available. Map isn't supported in this field.".format(source, rpr_field))
		write_own_property_log("Connection {} to {} isn't available. Map isn't supported for this field.".format(source, rpr_field))
		return 0

	return 1


def connectProperty(source_name, source_attr, rpr_name, rpr_attr):

	# full name of attribute
	source = source_name + "." + source_attr
	rpr_field = rpr_name + "." + rpr_attr

	try:
		cmds.connectAttr(source, rpr_field, force=True)
		write_own_property_log("Created connection from {} to {}.".format(source, rpr_field))
	except Exception as ex:
		print(ex)
		print("Connection {} to {} is failed.".format(source, rpr_field))
		write_own_property_log("Connection {} to {} is failed.".format(source, rpr_field))


# dispalcement convertion
def convertDisplacement(ai_sg, rpr_name):
	try:
		displacement = cmds.listConnections(ai_sg, type="displacementShader")
		if displacement:
			displacement_file = cmds.listConnections(displacement[0], type="file")
			if displacement_file:
				setProperty(rpr_name, "displacementEnable", 1)
				cmds.connectAttr(displacement_file[0] + ".outColor", rpr_name + ".displacementMap", f=True)
				copyProperty(rpr_name, displacement[0], "scale", "displacementMax")
	except Exception as ex:
		print(ex)
		print("Failed to convert displacement for {} material".format(rpr_name))


def convertaiAdd(ai, source):

	if cmds.objExists(ai + "_rpr"):
		rpr = ai + "_rpr"
	else:
		rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
		cmds.rename(rpr, ai + "_rpr")
		rpr = ai + "_rpr"

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

	if cmds.objExists(ai + "_rpr"):
		rpr = ai + "_rpr"
	else:
		rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
		cmds.rename(rpr, ai + "_rpr")
		rpr = ai + "_rpr"

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

	if cmds.objExists(ai + "_rpr"):
		rpr = ai + "_rpr"
	else:
		rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
		cmds.rename(rpr, ai + "_rpr")
		rpr = ai + "_rpr"

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
		"outColorB": "outZ"
	}

	rpr += "." + conversion_map[source]
	return rpr


def convertaiMultiply(ai, source):

	if cmds.objExists(ai + "_rpr"):
		rpr = ai + "_rpr"
	else:
		rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
		cmds.rename(rpr, ai + "_rpr")
		rpr = ai + "_rpr"

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

	if cmds.objExists(ai + "_rpr"):
		rpr = ai + "_rpr"
	else:
		rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
		cmds.rename(rpr, ai + "_rpr")
		rpr = ai + "_rpr"

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

	if cmds.objExists(ai + "_rpr"):
		rpr = ai + "_rpr"
	else:
		rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
		cmds.rename(rpr, ai + "_rpr")
		rpr = ai + "_rpr"

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

	if cmds.objExists(ai + "_rpr"):
		rpr = ai + "_rpr"
	else:
		rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
		cmds.rename(rpr, ai + "_rpr")
		rpr = ai + "_rpr"

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

	if cmds.objExists(ai + "_rpr"):
		rpr = ai + "_rpr"
	else:
		rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
		cmds.rename(rpr, ai + "_rpr")
		rpr = ai + "_rpr"

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

	if cmds.objExists(ai + "_rpr"):
		rpr = ai + "_rpr"
	else:
		rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
		cmds.rename(rpr, ai + "_rpr")
		rpr = ai + "_rpr"

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

	if cmds.objExists(ai + "_rpr"):
		rpr = ai + "_rpr"
	else:
		rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
		cmds.rename(rpr, ai + "_rpr")
		rpr = ai + "_rpr"

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

	if cmds.objExists(ai + "_rpr"):
		rpr = ai + "_rpr"
	else:
		rpr = cmds.shadingNode("RPRArithmetic", asUtility=True)
		cmds.rename(rpr, ai + "_rpr")
		rpr = ai + "_rpr"

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

	if cmds.objExists(ai + "_rpr"):
		rpr = ai + "_rpr"
	else:

		bump_type = getProperty(ai, "bumpInterp")
		if not bump_type:
			rpr = cmds.shadingNode("RPRBump", asUtility=True)
			cmds.rename(rpr, ai + "_rpr")
			rpr = ai + "_rpr"
		else:
			rpr = cmds.shadingNode("RPRNormal", asUtility=True)
			cmds.rename(rpr, ai + "_rpr")
			rpr = ai + "_rpr"

	# Logging to file
	start_log(ai, rpr)

	# Fields conversion
	try:
		bumpConnections = cmds.listConnections(ai + "." + "bumpValue", type="file")[0]
		if bumpConnections:
			cmds.connectAttr(bumpConnections + ".outColor", rpr + ".color", force=True)
	except Exception:
		print("Connection {} to {} failed. Check the connectors. ".format(bumpConnections + ".outColor", rpr + ".color"))
		write_own_property_log("Connection {} to {} failed. Check the connectors. ".format(bumpConnections + ".outColor", rpr + ".color"))

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


# Create default uber material for unsupported material
def convertUnsupportedMaterial(aiMaterial, source):

	materialSG = cmds.listConnections(aiMaterial, type="shadingEngine")
	# Check material exist
	if cmds.objExists(aiMaterial + "_rpr"):
		rprMaterial = aiMaterial + "_rpr"
	else:
		# Creating new Uber material
		rprMaterial = cmds.shadingNode("RPRUberMaterial", asShader=True)
		cmds.rename(rprMaterial, (aiMaterial + "_rpr"))
		rprMaterial = aiMaterial + "_rpr"

		# Check shading engine in aiMaterial
		if materialSG:
			sg = rprMaterial + "SG"
			cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
			cmds.connectAttr(rprMaterial + ".outColor", sg + ".surfaceShader", f=True)

	# Logging to file
	start_log(aiMaterial, rprMaterial)
	end_log(aiMaterial)

	if not materialSG:
		rprMaterial += "." + source
	return rprMaterial


#######################
## aiFlat 
#######################

def convertaiFlat(aiMaterial, source):

	materialSG = cmds.listConnections(aiMaterial, type="shadingEngine")
	# Check material exist
	if cmds.objExists(aiMaterial + "_rpr"):
		rprMaterial = aiMaterial + "_rpr"
	else:
		# Creating new Uber material
		rprMaterial = cmds.shadingNode("RPRFlatColorMaterial", asShader=True)
		cmds.rename(rprMaterial, (aiMaterial + "_rpr"))
		rprMaterial = aiMaterial + "_rpr"

		# Check shading engine in aiMaterial
		if materialSG:
			sg = rprMaterial + "SG"
			cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
			cmds.connectAttr(rprMaterial + ".outColor", sg + ".surfaceShader", f=True)

	# Enable properties, which are default in Arnold
	#
	#

	# Logging to file
	start_log(aiMaterial, rprMaterial)

	# Fields conversion
	copyProperty(rprMaterial, aiMaterial, "color", "color")

	# Logging in file
	end_log(aiMaterial)

	if not materialSG:
		rprMaterial += "." + source
	return rprMaterial


#######################
## aiMixShader 
#######################

def convertaiMixShader(aiMaterial, source):

	materialSG = cmds.listConnections(aiMaterial, type="shadingEngine")
	# Check material exist
	if cmds.objExists(aiMaterial + "_rpr"):
		rprMaterial = aiMaterial + "_rpr"
	else:
		# Creating new Uber material
		rprMaterial = cmds.shadingNode("RPRBlendMaterial", asShader=True)
		cmds.rename(rprMaterial, (aiMaterial + "_rpr"))
		rprMaterial = aiMaterial + "_rpr"

		# Check shading engine in aiMaterial
		if materialSG:
			sg = rprMaterial + "SG"
			cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
			cmds.connectAttr(rprMaterial + ".outColor", sg + ".surfaceShader", f=True)

	# Enable properties, which are default in Arnold
	#
	#

	# Logging to file
	start_log(aiMaterial, rprMaterial)

	# Fields conversion
	copyProperty(rprMaterial, aiMaterial, "color0", "shader1")
	copyProperty(rprMaterial, aiMaterial, "color1", "shader2")
	copyProperty(rprMaterial, aiMaterial, "weight", "mix")

	# Logging in file
	end_log(aiMaterial)

	if not materialSG:
		rprMaterial += "." + source
	return rprMaterial


#######################
## aiStandardSurface 
#######################

def convertaiStandardSurface(aiMaterial, source):

	materialSG = cmds.listConnections(aiMaterial, type="shadingEngine")
	# Check material exist
	if cmds.objExists(aiMaterial + "_rpr"):
		rprMaterial = aiMaterial + "_rpr"
	else:
		# Creating new Uber material
		rprMaterial = cmds.shadingNode("RPRUberMaterial", asShader=True)
		cmds.rename(rprMaterial, (aiMaterial + "_rpr"))
		rprMaterial = aiMaterial + "_rpr"

		# Check shading engine in aiMaterial
		if materialSG:
			sg = rprMaterial + "SG"
			cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
			cmds.connectAttr(rprMaterial + ".outColor", sg + ".surfaceShader", f=True)

			convertDisplacement(materialSG, rprMaterial)

	# Enable properties, which are default in Arnold
	defaultEnable(rprMaterial, aiMaterial, "diffuse", "base")
	defaultEnable(rprMaterial, aiMaterial, "reflections", "specular")
	defaultEnable(rprMaterial, aiMaterial, "refraction", "transmission")
	defaultEnable(rprMaterial, aiMaterial, "sssEnable", "subsurface")
	defaultEnable(rprMaterial, aiMaterial, "separateBackscatterColor", "subsurface")
	defaultEnable(rprMaterial, aiMaterial, "emissive", "emission")
	defaultEnable(rprMaterial, aiMaterial, "clearCoat", "coat")

	# Logging to file
	start_log(aiMaterial, rprMaterial)

	# Fields conversion
	copyProperty(rprMaterial, aiMaterial, "diffuseColor", "baseColor")
	copyProperty(rprMaterial, aiMaterial, "diffuseWeight", "base")
	copyProperty(rprMaterial, aiMaterial, "diffuseRoughness", "diffuseRoughness")

	metalness = getProperty(aiMaterial, "metalness")
	if metalness:
		setProperty(rprMaterial, "reflections", 1)
		setProperty(rprMaterial, "reflectMetalMaterial", 1)
		copyProperty(rprMaterial, aiMaterial, "reflectMetalness", "metalness")

	copyProperty(rprMaterial, aiMaterial, "reflectColor", "specularColor")
	copyProperty(rprMaterial, aiMaterial, "reflectWeight", "specular")
	copyProperty(rprMaterial, aiMaterial, "reflectRoughness", "specularRoughness")
	copyProperty(rprMaterial, aiMaterial, "reflectAnisotropy", "specularAnisotropy")
	copyProperty(rprMaterial, aiMaterial, "reflectAnisotropyRotation", "specularRotation")
	copyProperty(rprMaterial, aiMaterial, "reflectIOR", "specularIOR")

	copyProperty(rprMaterial, aiMaterial, "refractColor", "transmissionColor")
	copyProperty(rprMaterial, aiMaterial, "refractWeight", "transmission")
	copyProperty(rprMaterial, aiMaterial, "refractRoughness", "transmissionExtraRoughness")
	setProperty(rprMaterial, "refractThinSurface", getProperty(aiMaterial, "thinWalled"))

	copyProperty(rprMaterial, aiMaterial, "volumeScatter", "subsurfaceColor")
	copyProperty(rprMaterial, aiMaterial, "sssWeight", "subsurface")
	copyProperty(rprMaterial, aiMaterial, "backscatteringWeight", "subsurface")
	copyProperty(rprMaterial, aiMaterial, "subsurfaceRadius", "subsurfaceRadius")

	copyProperty(rprMaterial, aiMaterial, "coatColor", "coatColor")
	copyProperty(rprMaterial, aiMaterial, "coatWeight", "coat")
	copyProperty(rprMaterial, aiMaterial, "coatRoughness", "coatRoughness")
	copyProperty(rprMaterial, aiMaterial, "coatIor", "coatIOR")
	copyProperty(rprMaterial, aiMaterial, "coatNormal", "coatNormal")

	copyProperty(rprMaterial, aiMaterial, "emissiveColor", "emissionColor")
	copyProperty(rprMaterial, aiMaterial, "emissiveWeight", "emission")

	# Opacity convert. Material conversion doesn't support, because all aiMaterial have outColor, but we need outAlpha.
	ai_opacity = aiMaterial + ".opacity"
	rpr_opacity = rprMaterial + ".transparencyLevel"
	try:
		listConnections = cmds.listConnections(ai_opacity)
		if listConnections:
			obj, channel = cmds.connectionInfo(ai_opacity, sourceFromDestination=True).split('.')
			if cmds.objectType(obj) == "file":
				listConnectionsRPR = cmds.listConnections(rpr_opacity, type="RPRArithmetic")
				if not listConnectionsRPR:
					arithmetic = cmds.shadingNode("RPRArithmetic", asUtility=True)
				else:
					arithmetic = listConnectionsRPR[0]
				setProperty(arithmetic, "operation", 1)
				setProperty(arithmetic, "inputA", (1, 1, 1))
				connectProperty(obj, channel, arithmetic, "inputB")
				connectProperty(arithmetic, "outX", rprMaterial, "transparencyLevel")
			else:
				source = obj + "." + channel
				print("Connection {} to {} isn't available. This source isn't supported in this field.".format(source, rpr_opacity))
				write_own_property_log("Connection {} to {} isn't available. This source isn't supported for this field.".format(source, rpr_opacity))
		else:
			ai_opacity = getProperty(aiMaterial, "opacity")
			max_value = 1 - max(ai_opacity)
			setProperty(rprMaterial, "transparencyLevel", max_value)
		setProperty(rprMaterial, "transparencyEnable", 1)
	except Exception as ex:
		print(ex)
		print("Conversion {} to {} is failed. Check this material. ".format(source, rpr_opacity))
		write_own_property_log("Conversion {} to {} is failed. Check this material. ".format(source, rpr_opacity))

	try:
		bumpConnections = cmds.listConnections(aiMaterial + ".normalCamera")
		if bumpConnections:
			setProperty(rprMaterial, "normalMapEnable", 1)
			copyProperty(rprMaterial, aiMaterial, "normalMap", "normalCamera")
	except Exception as ex:
		print(ex)
		print("Failed to convert bump.")
		write_own_property_log("Failed to convert bump.")

	# Logging in file
	end_log(aiMaterial)

	if not materialSG:
		rprMaterial += "." + source
	return rprMaterial


#######################
## aiStandardVolume 
#######################

def convertaiStandardVolume(aiMaterial, source):

	materialSG = cmds.listConnections(aiMaterial, type="shadingEngine")
	# Check material exist
	if cmds.objExists(aiMaterial + "_rpr"):
		rprMaterial = aiMaterial + "_rpr"
	else:
		# Creating new Uber material
		rprMaterial = cmds.shadingNode("RPRVolumeMaterial", asShader=True)
		cmds.rename(rprMaterial, (aiMaterial + "_rpr"))
		rprMaterial = aiMaterial + "_rpr"

		# Check shading engine in aiMaterial
		if materialSG:
			sg = rprMaterial + "SG"
			cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
			cmds.connectAttr(rprMaterial + ".outColor", sg + ".surfaceShader", f=True)

	# Enable properties, which are default in Arnold
	#
	#

	# Logging to file
	start_log(aiMaterial, rprMaterial)

	# Fields conversion
	copyProperty(rprMaterial, aiMaterial, "scatterColor", "scatterColor")
	copyProperty(rprMaterial, aiMaterial, "emissionColor", "emissionColor")
	copyProperty(rprMaterial, aiMaterial, "transmissionColor", "transparent")
	copyProperty(rprMaterial, aiMaterial, "density", "density")

	# Logging in file
	end_log(aiMaterial)

	if not materialSG:
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
	setProperty(iblShape, "intensity", 1 * 2 ** exposure)

	# Copy properties from ai dome light
	domeTransform = cmds.listRelatives(dome_light, p=True)[0]
	setProperty(iblTransform, "rotateY", getProperty(domeTransform, "rotateY") + 180)
	
	try:
		file = cmds.listConnections(dome_light + ".color")
		if file:
			ibl_map = getProperty(file[0], "fileTextureName")
			print(ibl_map)
			cmds.setAttr(iblTransform + ".filePath", ibl_map, type="string")
	except Exception as ex:
		print(ex)
		print("Failed to convert map from Arnold Dome light")
		   
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

	try:
		file = cmds.listConnections(sky, "color")[0]
		if file:
			ibl_map = getProperty(file, "fileTextureName")
			cmds.setAttr(iblTransform + ".filePath", ibl_map, type="string")
	except Exception as ex:
		print(ex)
		print("Failed to convert map from Arnold Sky")
		   
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

	# Redshift light transform
	aiTransform = cmds.listRelatives(ai_light, p=True)[0]
	aiLightShape = ai_light.split("|")[-1]

	if cmds.objExists(aiLightShape + "_rpr"):
		rprLightShape = aiLightShape + "_rpr"
		rprTransform = cmds.listRelatives(rprLightShape, p=True)[0]
	else: 
		rprLightShape = cmds.createNode("RPRIES", n="RPRIESLight")
		cmds.rename(rprLightShape, aiLightShape + "_rpr")
		rprLightShape = aiLightShape + "_rpr"
		rprTransform = cmds.listRelatives(rprLightShape, p=True)[0]
		cmds.rename(rprTransform, aiTransform + "_rpr")
		rprTransform = aiTransform + "_rpr"

	# Logging to file 
	start_log(aiLightShape, rprLightShape)

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

	try:
		ies = getProperty(ai_light, "aiFilename")
		cmds.setAttr(rprLightShape + ".iesFile", ies, type="string")
	except Exception as ex:
		print(ex)
		print("Failed to convert map from Redshift IES light")

	# Logging to file
	end_log(aiLightShape) 


def convertaiAreaLight(ai_light):

	# Redshift light transform
	aiTransform = cmds.listRelatives(ai_light, p=True)[0]
	aiLightShape = ai_light.split("|")[-1]

	if cmds.objExists(aiLightShape + "_rpr"):
		rprLightShape = aiLightShape + "_rpr"
		rprTransform = cmds.listRelatives(rprLightShape, p=True)[0]
	else: 
		rprLightShape = cmds.createNode("RPRPhysicalLight", n="RPRPhysicalLightShape")
		cmds.rename(rprLightShape, aiLightShape + "_rpr")
		rprLightShape = aiLightShape + "_rpr"
		rprTransform = cmds.listRelatives(rprLightShape, p=True)[0]
		cmds.rename(rprTransform, aiTransform + "_rpr")
		rprTransform = aiTransform + "_rpr"

	# Logging to file 
	start_log(aiLightShape, rprLightShape)

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
	end_log(aiLightShape)  


def convertaiMeshLight(ai_light):

	# Redshift light transform
	aiTransform = cmds.listRelatives(ai_light, p=True)[0]
	aiLightShape = ai_light.split("|")[-1]

	if cmds.objExists(aiLightShape + "_rpr"):
		rprLightShape = aiLightShape + "_rpr"
		rprTransform = cmds.listRelatives(rprLightShape, p=True)[0]
	else: 
		rprLightShape = cmds.createNode("RPRPhysicalLight", n="RPRPhysicalLightShape")
		cmds.rename(rprLightShape, aiLightShape + "_rpr")
		rprLightShape = aiLightShape + "_rpr"
		rprTransform = cmds.listRelatives(rprLightShape, p=True)[0]
		cmds.rename(rprTransform, aiTransform + "_rpr")
		rprTransform = aiTransform + "_rpr"

	# Logging to file 
	start_log(aiLightShape, rprLightShape)

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
		print(ex)
		print("Failed to convert mesh in Physical light")

	# Logging to file
	end_log(aiLightShape)


# Convert material. Returns new material name.
def convertaiMaterial(aiMaterial, source):

	ai_type = cmds.objectType(aiMaterial)

	conversion_func = {
		"aiAmbientOcclusion": convertUnsupportedMaterial,
		"aiCarPaint": convertUnsupportedMaterial,
		"aiFlat": convertaiFlat,
		"aiLayerShader": convertUnsupportedMaterial,
		"aiMatte": convertUnsupportedMaterial,
		"aiMixShader": convertaiMixShader,
		"aiPassthrough": convertUnsupportedMaterial,
		"aiRaySwitch": convertUnsupportedMaterial,
		"aiShadowMatte": convertUnsupportedMaterial,
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
		#"aiBump2d": convertaiBump2d,
		#"aiBump3d": convertaiBump3d,
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
		"multiplyDivide": convertmultiplyDivide
	}

	if ai_type in conversion_func:
		rpr = conversion_func[ai_type](aiMaterial, source)
	else:
		if source:
			rpr = aiMaterial + "." + source
		else:
			rpr = ""

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


def searchArnoldType(obj):

	if cmds.objExists(obj):
		objType = cmds.objectType(obj)
		if "ai" in objType:
			return 1
	return 0


def cleanScene():

	listMaterials= cmds.ls(materials=True)
	for material in listMaterials:
		if searchArnoldType(material):
			shEng = cmds.listConnections(material, type="shadingEngine")
			try:
				cmds.delete(shEng[0])
				cmds.delete(material)
			except Exception as ex:
				print(ex)

	listLights = cmds.ls(l=True, type=["aiAreaLight", "aiMeshLight", "aiPhotometricLight", "aiSkyDomeLight"])
	for light in listLights:
		transform = cmds.listRelatives(light, p=True)[0]
		try:
			cmds.delete(light)
			cmds.delete(transform)
		except Exception as ex:
			print(ex)

	listObjects = cmds.ls(l=True)
	for obj in listObjects:
		if searchArnoldType(object):
			try:
				cmds.delete(obj)
			except Exception as ex:
				print(ex)


def checkSG(material):

	if searchArnoldType(material):
		SGs = cmds.listConnections(material, type="shadingEngine")
		if SGs:
			return 1
	return 0


def defaultEnable(RPRmaterial, aiMaterial, enable, value):

	weight = cmds.getAttr(aiMaterial + "." + value)
	if weight > 0:
		cmds.setAttr(RPRmaterial + "." + enable, 1)
	else:
		cmds.setAttr(RPRmaterial + "." + enable, 0)


def convertScene():

	# Check plugins
	if not cmds.pluginInfo("mtoa", q=True, loaded=True):
		cmds.loadPlugin("mtoa")

	if not cmds.pluginInfo("RadeonProRender", q=True, loaded=True):
		cmds.loadPlugin("RadeonProRender")

	# Convert ArnoldEnvironment
	'''
	env = cmds.ls(type="aiEnvironment")
	if env:
		try:
			convertaiEnvironment(env[0])
		except Exception as ex:
			print(ex)
			print("Error while converting environment. ")
	'''

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
			print(ex)
			print("Error while converting physical sky. \n")

	
	# Get all lights from scene
	listLights = cmds.ls(l=True, type=["aiAreaLight", "aiMeshLight", "aiPhotometricLight", "aiSkyDomeLight"])

	# Convert lights
	for light in listLights:
		try:
			convertLight(light)
		except Exception as ex:
			print(ex)
			print("Error while converting {} light. \n".format(light))
		

	# Get all materials from scene
	listMaterials = cmds.ls(materials=True)
	materialsDict = {}
	for each in listMaterials:
		if checkSG(each):
			materialsDict[each] = convertaiMaterial(each, "")

	for ai, rpr in materialsDict.items():
		try:
			cmds.hyperShade(objects=ai)
			rpr_sg = cmds.listConnections(rpr, type="shadingEngine")[0]
			cmds.sets(e=True, forceElement=rpr_sg)
		except Exception as ex:
			print("Error while converting {} material. \n".format(ai))
	
	cmds.setAttr("defaultRenderGlobals.currentRenderer", "FireRender", type="string")
	setProperty("defaultRenderGlobals", "imageFormat", 8)
	#setProperty("RadeonProRenderGlobals", "completionCriteriaIterations", getProperty("???", "???"))


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