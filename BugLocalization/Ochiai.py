import os, sys
import argparse
import pickle
import json
import subprocess, resource
import math
import time

def Ochiai(base: set, buggies: list, nonbuggies: list):
    """
    """

    (
        ef_entityId2value,
        nf_entityId2value,
        ep_entityId2value,
        entityId2statement
    ) = compute_ef_nf_ep(base, buggies, nonbuggies)

    entityId2suspicious = {}

    for entityId, statement in entityId2statement.items():
        ef = ef_entityId2value[entityId]
        nf = nf_entityId2value[entityId]
        ep = ep_entityId2value[entityId]

        suspicious = ef / math.sqrt((ef+nf)*(ef+ep))

        entityId2suspicious[entityId] = suspicious
        
        # DEBUG
        #print (f"statement: {statement}; ef: {ef}; nf: {nf}; ep: {ep}")
        #if ep != 1:
        #    print (f"   ep != 1: statement: {statement}; ef: {ef}; nf: {nf}; ep: {ep}")

    return entityId2suspicious, entityId2statement

def compute_ef_nf_ep(base: set, buggies: list, nonbuggies: list):
    """
    """

    entityId2statement = {}

    ef_entityId2value = {}
    nf_entityId2value = {}
    ep_entityId2value = {}

    entityId = 0
    for statement in base:
        entityId2statement[entityId] = statement

        ef_entityId2value[entityId] = 1
        nf_entityId2value[entityId] = 0
        ep_entityId2value[entityId] = 0

        for statements in buggies:
            if statement in statements:
                ef_entityId2value[entityId] += 1
            else:
                nf_entityId2value[entityId] += 1

        for statements in nonbuggies:
            if statement in statements:
                ep_entityId2value[entityId] += 1

        entityId += 1

    return (
            ef_entityId2value, 
            nf_entityId2value, 
            ep_entityId2value, 
            entityId2statement
    )
