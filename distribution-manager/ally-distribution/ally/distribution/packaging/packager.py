'''
Created on Sep 30, 2013
 
@package: distribution manager
@copyright: 2013 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Cristian Domsa
 
Simple implementation for distribution manager project.
'''

from ally.container.ioc import injected
import logging
import os
import sys
from types import ModuleType
from .builder import Builder

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

SETUP_FILENAME = 'setup.py'
SETUP_TEMPLATE_BEGIN = '''
\'\'\'
Created on Oct 1, 2013
 
@package: distribution_manager
@copyright: 2013 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Cristian Domsa
 
Setup configuration for components/plugins needed for pypi.
\'\'\'

# --------------------------------------------------------------------

from setuptools import setup, find_packages

# --------------------------------------------------------------------

setup('''
SETUP_TEMPLATE_END = '''packages=find_packages('.'),
      platforms=['all'],
      zip_safe=True,
      license='GPL v3',
      url='http://www.sourcefabric.org/en/superdesk/', # project home page
      )
'''
IGNORE_DIRS = ['__pycache__']
ATTRIBUTE_MAPPING = {'NAME'            : 'name',
                     'VERSION'         : 'version',
                     'AUTHOR'          : 'author',
                     'AUTHOR_EMAIL'    : 'author_email',
                     'KEYWORDS'        : 'keywords',
                     'INSTALL_REQUIRES': 'install_requires',
                     'DESCRIPTION'     : 'description',
                     'LONG_DESCRIPTION': 'long_description',
                     'TEST_SUITE'      : 'test_suite',
                     'CLASSIFIERS'     : 'classifiers',
                     }
EXTRA_DICT_ATT = '__extra__'

# --------------------------------------------------------------------

@injected
class Packager:
    '''
    @todo: update description
    Distribution class for managing requirements, deploy path
    '''
    
    pathSource = str
    # The path where the components/plugins are located.
    folderType = str
    # type of folder to look for configuration __init__ file 
    # __setup__ for components
    # __plugin__ for plugins
    destFolder = str
    #destination folder to deploy distribution
    
    def __init__(self):
        assert isinstance(self.pathSource, str), 'Invalid path provided %s' % self.pathSource
        assert isinstance(self.folderType, str), 'Invalid folderType provided %s' % self.folderType

    def getDirs(self, path):
        '''
        returns the list of directories filtering out IGNORE_DIRS
        '''
        children = os.listdir(path)
        return [child for child in children if os.path.isdir(os.path.join(path, child)) 
                                            and child not in IGNORE_DIRS]

    def constructDict(self, module):
        '''
        returns the dict containing information contained in __init__ file
        @purpose: setuptools 
        '''
        
        assert isinstance(module, ModuleType), 'Invalid module name %s' % module
        setupDict = {}
        for attribute, value in ATTRIBUTE_MAPPING.items():
            if hasattr(module, attribute):
                setupDict[value] = getattr(module, attribute)
        if hasattr(module, EXTRA_DICT_ATT):
            setupDict.update(getattr(module, EXTRA_DICT_ATT))
        return setupDict
    
    def writeSetupFile(self, path, info):
        '''
        Writes setup.py file to path
        '''
        filename = os.path.abspath(os.path.join(path, SETUP_FILENAME))
        with open(filename, 'w') as f:
            f.write(SETUP_TEMPLATE_BEGIN)
            for attribute in info:
                f.write(attribute + '=' + repr(info[attribute]) + ',\n')
            f.write(SETUP_TEMPLATE_END)
        f.close()
 
    def generateSetupFiles(self):
        
        all = success = failed = 0
        components = self.getDirs(self.pathSource)
 
        for packageName in components:
            all += 1
            
            assert log.info('-' * 50) or True
            assert log.info('*** Package name *** {0} ***'.format(packageName)) or True
            
            packagePath = os.path.join(self.pathSource, packageName)
            egg_builder = Builder(packagePath, packageName)
            
            if self.folderType in self.getDirs(packagePath):
                setupPath = os.path.join(self.pathSource, packageName, self.folderType)
                setupDirs = self.getDirs(setupPath)
                sys.path.append(os.path.abspath(setupPath))
                if len(setupDirs) != 1:
                    assert log.info('''No setup module to configure or 
                            more than one setup module in this package 
                            *** SKIPING *** {0) ***'''.format(packageName)) or True
                    continue
                else:
                    setupModule = setupDirs[0] 
                    try:
                        module = __import__(setupModule, locals=locals(), globals=globals())
                        try:
                            
                            info = self.constructDict(module)
                            info['name'] = packageName
                            assert log.info('*** Setup info import from module {0} *** OK'.format(module.__name__)) or True
                            try:
                                self.writeSetupFile(packagePath, info)
                                assert log.info('*** Setup file succesfully writen *** {0} *** OK'.format(packagePath)) or True
                                try:
                                    egg_builder.generateEggFile()
                                    assert log.info('*** Egg file succesfully deployed *** {0} *** OK'.format(packageName)) or True
                                except:
                                    assert log.info('*** Egg file failed to deploy *** {0} *** NOK'.format(packageName)) or True
                            except:
                                assert log.info('*** Setup file writing failed *** {0} *** NOK'.format(packageName)) or True
                        except:
                            assert log.info('*** info import from module {0} *** NOK'.format(module)) or True
                        assert log.info('*** Setup module *** {0} *** OK'.format(setupModule)) or True
                        success += 1
                    except: 
                        assert log.info('*** Setup module *** {0} *** NOK'.format(setupModule)) or True
                        failed += 1

        assert log.info('-' * 50) or True                
        assert log.info('All components: {0}'.format(all)) or True
        assert log.info('Succeded: {0}'.format(success)) or True
        assert log.info('Failed: {0}'.format(failed)) or True