#!/usr/bin/python

"""##################################################################
# Helper class that contains the Var (variant) object class; also
#   carries out variant-related functions (e.g. formatting)
#
# Note to self:
#   - For now, only the detailed annotation and snp will be searched;
#       the rest will be print directly to output without any
#       intermediate manipualtions
#       - This means that the genes will not have to be split
#   - Probably should combine IdList and recordLib into a single variable
#       since recordLib is just an extension of IdList, hmmmmmmmm
#   - Not sure how to handle non-existing information workflow. Keep it as
#       a NoneType, or make user manually check?
#
# Author: Anthony Chen
##################################################################"""
import sys

class Var:
    #Class constructor and attributes
    def __init__(self, chromo, pos, gene, func_type, anno, snp):
        #Content from file
        self.chromosome = chromo
        self.position = pos
        self.gene = gene #Gene symbol
        self.function_type = func_type #Function type
        self.annotation = anno #Detailed variant annotation
        self.snp = snp #All SNPs
        #Pre-search program-created contents
        self.searchable = True #Whether it is a wanted variant (yes for now)
        self.anno_list = None #Formatted list of annotation(s)
        #Post eSearch attributes
        self.IdList = None
        #Post eSummary attributes
        self.recordLib = None
    ########## Object methods ##########
    #Method to output the clinical significance
    def output_clin_sig(self):
        #If the variant was not searched, indicate to user
        if self.searchable == False:
            return "Variant not searched"
        #If there are no clinical significance, output No items found
        if self.recordLib == None:
            return "No items found"
        #Check to see if any ClinVar IDs returned an invalid variable type
        if None in [info['clin_sig'] for key,info in self.recordLib.iteritems()]:
            return "<ERROR> Unexpected events. Manual search recommended."
        #Join all clinical significance, separated by square brackets
        #   Also replace using colons to prevent comma-separation
        clinSig = ']['.join([info['clin_sig'] for key,info in self.recordLib.iteritems()])
        return ("[%s]"%(clinSig)).replace('][',']|[').replace(',',';')

    #Method to output the condition
    def output_conditions(self):
        #If the variant was not searched, return empty string
        if self.searchable == False:
            return ""
        #If there are no conditions found, output an empty string
        if self.recordLib == None:
            return ""
        #Try to join all conditions together, separated by square brackets
        try:
            output_cond = ""
            for key, info in self.recordLib.iteritems():
                output_cond += "[%s]"%(']['.join(c for c in info['cond']))
        #If a Nonetype is initiated for any of the conditions
        except TypeError:
            #Return an empty string
            return ""
        #If no exception, return the conditions, with additional pipe ('|')
        #   delimeter; also replace commas using colons to prevent comma-separation
        return output_cond.replace('][',']|[').replace(',',';')


#Goes through the entire variant list for pre-search formatting
def format_variantList(v_list):
    #Initiate a list of genes
    wanted_genes = []

    #Check for the presence of filter genes in local directory
    #   If such file is found, ask user if they wish to filter by genes
    apply_gene_filter = initiate_filter_genes(wanted_genes)

    #User indication
    print "[Program] Apply gene filter: %s." % str(apply_gene_filter)

    #Iterate through list of variants to format variants
    for i in range(0,len(v_list)):
        #Split (potential) multiple genes by the "|" delimiter
        v_list[i].anno_list = v_list[i].annotation.split("|")

        #Iterate through each annotation to delete the ones not containing a wanted gene
        if apply_gene_filter:
            #Initiate a list of annotations to delete from this variant
            toDelete_list = []

            #Iterate through each (currently un-processed) individual annotation
            #TODO; make below cleaner via list comprehension???
            for raw_anno in v_list[i].anno_list:
                if not any(s in raw_anno for s in wanted_genes):
                    toDelete_list.append(raw_anno)

            #Delete the annotations that do not have the genes we want
            for del_anno in toDelete_list:
                if del_anno in v_list[i].anno_list:
                    v_list[i].anno_list.remove(del_anno)

            #Delete the temp list for memory
            del toDelete_list

        #Iterate through each annotation to format them properly for search
        for j in range(0, len(v_list[i].anno_list)):
            #BUG: also something wrong with below when filtering genes, due to pop function
            #BUG: need to do gene filtering in a different way
            v_list[i].anno_list[j] = format_annotation(v_list[i].anno_list[j])

    #Iterate through the list again to check for searchability (i.e. if anything is filtered out)
    for i in range(0,len(v_list)):
        #If a variant has no annotations left to be searched, it is not searchable
        if len(v_list[i].anno_list) == 0:
            v_list[i].searchable = False

    #Return success
    return 0

#Looks for a reads a list of wanted genes from the local directory
def initiate_filter_genes(gene_list):
    #Attempt to open the input stream
    try:
        f = open("Wanted_Genes.txt", 'r')
    #Except for I/O error in case file is not present
    except IOError: return False
    #If the file is found, read it
    gene_list += f.readlines()
    #Strip off the nextline characters
    for i in range(0, len(gene_list)):
        gene_list[i] = gene_list[i].strip()
    #Prompt the user to see if they want to use the gene filter
    print "[Program] Detected file 'Wanted_Genes.txt' in local directory, with %d genes inside." % (len(gene_list))
    while (True):
        usr_in = raw_input('Would you like to initiate gene filtering? [y/n]: ')
        if usr_in == 'y': return True
        if usr_in == 'n': return False
        #If input not valid, try again
        print "[ERROR] Invalid input. Try again."



#Function that formats an individual annotations
""" FEEL FREE TO CHANGE BELOW """
#TODO: the below is problematic, especially for handling non 'NM' variants
#TODO: either check for functional types, only check first annotation and/or
#TODO:  use other metrics to format the search term

def format_annotation(raw_anno):
    #Shorten the exon formatting, if present
    good_anno = raw_anno.replace(":exon",".")
    #If it contains brackets, just return what is now in the bracket
    try:
        good_anno = good_anno[good_anno.index('(')+1:good_anno.index(')')]
        return good_anno
    except ValueError: pass
    #Else, remove everything before the "NM"
    good_anno = good_anno[good_anno.find("NM"):]
    #Remove the protein mutations, if present
    try:
        good_anno = good_anno[:good_anno.index(":p")]
    except ValueError: pass
    #Change the point mutation format, if present
    #   In essense, change something such as C123A to 123C>A
    try:
        mutList = list(good_anno[good_anno.index(":c.")+3:]) #Get a char array of point mutation
        mut = ''.join(mutList[1:len(mutList)-1]) #Get the numbers
        mut += "%s>%s" % (mutList[0], mutList[len(mutList)-1]) #Get the changes to the nucleotide
        good_anno = good_anno[:good_anno.index(':c.')+3] + mut #Append all together
    except ValueError: pass
    #Return the formatted annotation
    return good_anno
